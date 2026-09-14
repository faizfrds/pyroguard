"""PyroGuard AI Discord Bot with Interactive Slash Commands.

Allows disaster response teams and forestry officers to query fire risk,
active VIIRS thermal anomalies, and ReAct agent intelligence directly in Discord channels.
"""

import os
import sys
import logging
from typing import List
from dotenv import load_dotenv

import discord
from discord import app_commands

# Ensure backend path is loaded
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.domain.indonesia import REGIONS_REGISTRY, resolve_region
from app.agent.tools import (
    tool_extract_regional_fire_metrics,
    tool_fetch_active_hotspots,
    tool_forecast_wildfire_risk
)
from app.agent.engine import PyroGuardAgentEngine

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("pyroguard_bot")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Discord color map based on risk tier
TIER_COLORS = {
    "CRITICAL": 0xDC2626,  # Bright Red
    "HIGH": 0xEA580C,      # Orange
    "MODERATE": 0xCA8A04,  # Yellow/Gold
    "LOW": 0x16A34A        # Green
}


# Region autocomplete handler
async def region_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> List[app_commands.Choice[str]]:
    choices = []
    for key, data in REGIONS_REGISTRY.items():
        label = f"{data['name']} ({data['province']})"
        if current.lower() in label.lower():
            choices.append(app_commands.Choice(name=label, value=data["name"]))
    return choices[:10]


@client.event
async def on_ready():
    logger.info(f"PyroGuard Discord Bot logged in as {client.user} (ID: {client.user.id})")
    # Sync slash commands globally
    try:
        synced = await tree.sync()
        logger.info(f"Successfully synced {len(synced)} slash commands globally.")
    except Exception as e:
        logger.error(f"Failed to sync slash commands: {e}")


# Command 1: /risk
@tree.command(name="risk", description="Assess 14-day wildfire vulnerability index, fuel moisture, and tactical advisories.")
@app_commands.autocomplete(region=region_autocomplete)
@app_commands.describe(region="Target Indonesian regency, province, or national park (e.g. Mount Bromo, Kapuas)")
async def slash_risk(interaction: discord.Interaction, region: str):
    await interaction.response.defer(thinking=True)

    try:
        reg_data = resolve_region(region)
        region_name = reg_data["name"]

        # Run multi-sensor extraction & ONNX inference
        metrics = await tool_extract_regional_fire_metrics(region_name=region_name, lookback_days=30)
        forecast = await tool_forecast_wildfire_risk(metrics_payload=metrics, forecast_horizon_days=14)

        tier = forecast["risk_tier"]
        wvi = forecast["wildfire_vulnerability_index"]
        color = TIER_COLORS.get(tier, 0xEA580C)
        is_peat = reg_data.get("peatland_pct", 0) > 30.0

        embed = discord.Embed(
            title=f"🔥 Wildfire Risk Assessment: {region_name}",
            description=f"**Province**: {reg_data['province']} | **Ecosystem**: {reg_data.get('ecosystem_type', 'Tropical Forest')}",
            color=color
        )

        # Risk Score & Status
        embed.add_field(name="Vulnerability Index", value=f"**{wvi} / 1.00** ({tier})", inline=True)
        
        if is_peat:
            pdi = metrics["peatland_drying_index"]
            embed.add_field(name="Peat Water Table", value=f"**{pdi['estimated_water_table_cm']} cm** ({pdi['status']})", inline=True)
        else:
            embed.add_field(name="Soil & Surface Regime", value="**Volcanic / Mineral Savanna**", inline=True)

        embed.add_field(name="14d Dry Spell", value=f"{forecast['weather_summary']['consecutive_dry_days']} days (<1mm rain)", inline=True)

        # Telemetry Deltas
        d14 = metrics["delta_14d"]
        telemetry_txt = (
            f"• **Sentinel-1 SAR**: {d14['sar_vv_drop_db']} dB drop (Surface moisture drawdown)\n"
            f"• **Sentinel-2 NDWI**: {d14['ndwi_change_pct']}% (Canopy water loss)\n"
            f"• **Thermal LST**: +{d14['lst_anomaly_celsius']} °C above seasonal normal\n"
            f"• **Peak Temp**: {forecast['weather_summary']['max_temp_avg_c']} °C"
        )
        embed.add_field(name="📡 Remote Sensing Telemetry (14d)", value=telemetry_txt, inline=False)

        # Top Drivers
        drivers_txt = "\n".join(
            f"• **{d['feature']}** ({d['contribution_pct']}%)"
            for d in forecast["top_drivers"][:3]
        )
        embed.add_field(name="📊 Top Contributing Risk Drivers", value=drivers_txt, inline=False)

        # Advisory
        embed.add_field(name="🚨 Tactical Advisory", value=forecast["recommended_advisory"], inline=False)
        embed.set_footer(text="PyroGuard AI • Sentinel-1/2 GEE + ONNX Neural Risk Forecaster")

        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Error handling /risk: {e}")
        await interaction.followup.send(f"❌ Error evaluating wildfire risk: `{str(e)}`")


# Command 2: /hotspots
@tree.command(name="hotspots", description="Query near-real-time NASA FIRMS (VIIRS 375m) thermal anomalies and smoke plume projections.")
@app_commands.autocomplete(region=region_autocomplete)
@app_commands.describe(
    region="Target Indonesian regency or national park",
    lookback_days="Number of days to look back (1 to 7, default: 3)"
)
async def slash_hotspots(interaction: discord.Interaction, region: str, lookback_days: int = 3):
    await interaction.response.defer(thinking=True)

    try:
        reg_data = resolve_region(region)
        region_name = reg_data["name"]

        hotspots_data = await tool_fetch_active_hotspots(region_name=region_name, lookback_days=lookback_days)
        total = hotspots_data["total_hotspots"]
        peat_count = hotspots_data["peatland_hotspots"]
        total_frp = hotspots_data["total_frp_mw"]
        max_frp = hotspots_data["max_frp_mw"]

        color = 0xDC2626 if total > 0 else 0x16A34A

        embed = discord.Embed(
            title=f"🛰️ Active Thermal Anomalies: {region_name}",
            description=f"**Source**: {hotspots_data['source']} | **Window**: Past {lookback_days} days",
            color=color
        )

        embed.add_field(name="Total Hotspots", value=f"**{total} detections**", inline=True)
        embed.add_field(name="In Peat / Protected Zone", value=f"**{peat_count}**", inline=True)
        embed.add_field(name="Fire Radiative Power", value=f"Max: **{max_frp} MW**\nTotal: {total_frp} MW", inline=True)

        if total > 0:
            sample_list = []
            for h in hotspots_data["hotspots"][:4]:
                sample_list.append(
                    f"• `[{h['latitude']}, {h['longitude']}]` FRP: **{h['frp_mw']} MW** ({h['confidence']} conf) — {h['khg_name']}"
                )
            embed.add_field(name="🔥 Thermal Coordinates Sample", value="\n".join(sample_list), inline=False)
            embed.add_field(name="💨 Haze Trajectory", value="Smoke cones projected downwind via dominant wind vector U/V field.", inline=False)

        embed.set_footer(text="PyroGuard AI • NASA FIRMS VIIRS 375m & KLHK Peatland Integration")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Error handling /hotspots: {e}")
        await interaction.followup.send(f"❌ Error fetching hotspots: `{str(e)}`")


# Command 3: /ask
@tree.command(name="ask", description="Ask the autonomous PyroGuard ReAct agent an operational disaster question.")
@app_commands.describe(query="Your question (e.g. 'Evaluate fire risk at Mount Bromo near tourist areas')")
async def slash_ask(interaction: discord.Interaction, query: str):
    await interaction.response.defer(thinking=True)

    try:
        engine = PyroGuardAgentEngine()
        result = await engine.execute_query(query=query)

        embed = discord.Embed(
            title=f"🤖 PyroGuard Agent Intelligence Report",
            description=f"**Target**: {result['region_name']} ({result['province']})\n**Risk Tier**: **{result['risk_tier']}** (WVI: {result['risk_score']})",
            color=TIER_COLORS.get(result["risk_tier"], 0xEA580C)
        )

        # Truncate markdown nicely if exceeds Discord's 4096 character limit
        report_text = result["report_markdown"]
        if len(report_text) > 2000:
            report_text = report_text[:1990] + "\n\n*(Report truncated for Discord embed limit)*"

        embed.add_field(name="Executive Briefing", value=report_text, inline=False)
        embed.set_footer(text="PyroGuard AI Autonomous ReAct Agent")

        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"Error handling /ask: {e}")
        await interaction.followup.send(f"❌ Agent execution encountered an error: `{str(e)}`")


# Command 4: /regions
@tree.command(name="regions", description="List supported priority disaster zones, peatland domes, and national parks.")
async def slash_regions(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📍 PyroGuard AI Monitored Regions",
        description="High-priority wildfire observation areas across Indonesian provinces:",
        color=0x38BDF8
    )

    for key, data in REGIONS_REGISTRY.items():
        embed.add_field(
            name=f"{data['name']} ({data['province']})",
            value=f"Ecosystem: {data.get('ecosystem_type', 'Peat Swamp')}\nPeat Area: {data['peatland_pct']}%\nCoordinates: `{data['center']}`",
            inline=True
        )

    embed.set_footer(text="PyroGuard AI • All-Indonesia Wildfire Intelligence")
    await interaction.response.send_message(embed=embed)


def run_bot():
    token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    if not token or token == "your_copied_bot_token_here":
        print("\n❌ DISCORD_BOT_TOKEN is not set in your .env file!")
        print("Please add: DISCORD_BOT_TOKEN=your_token in .env to launch the Discord bot.\n")
        return
    client.run(token)


if __name__ == "__main__":
    run_bot()

