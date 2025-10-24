#!/usr/bin/env python3
"""CLI tool for managing external API providers."""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import click

from agents.core.external_api_config import (
    ProviderConfig,
    ProviderType,
    get_config,
    reset_config,
)
from agents.core.smart_model_selector import get_smart_selector
from agents.core.unified_model_adapter import ModelProviderFactory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """External API Provider Management CLI."""
    pass


@cli.command()
@click.option("--config-file", "-c", help="Configuration file path")
def status(config_file: Optional[str]):
    """Show current provider status."""
    if config_file:
        # Reset global config and load from specified file
        reset_config()
        from agents.core.external_api_config import ExternalAPIConfig

        config = ExternalAPIConfig(config_file)
    else:
        config = get_config()

    click.echo("🔍 External API Provider Status")
    click.echo("=" * 40)

    # Show configuration stats
    stats = config.get_stats()
    click.echo(f"Total providers: {stats['total_providers']}")
    click.echo(f"Enabled providers: {stats['enabled_providers']}")
    click.echo(f"Default provider: {stats['default_provider'] or 'None'}")
    click.echo()

    # Show provider details
    if config.providers:
        click.echo("📋 Provider Details:")
        for name, provider_config in config.providers.items():
            status_icon = "✅" if provider_config.enabled else "❌"
            click.echo(f"  {status_icon} {name}")
            click.echo(f"    Type: {provider_config.provider_type.value}")
            click.echo(f"    Model: {provider_config.model}")
            click.echo(f"    Timeout: {provider_config.timeout}s")
            click.echo(f"    Max tokens: {provider_config.max_tokens}")
            click.echo(f"    Temperature: {provider_config.temperature}")
            click.echo()
    else:
        click.echo("No providers configured.")


@cli.command()
@click.option("--config-file", "-c", help="Configuration file path")
def validate(config_file: Optional[str]):
    """Validate current configuration."""
    if config_file:
        reset_config()
        from agents.core.external_api_config import ExternalAPIConfig

        config = ExternalAPIConfig(config_file)
    else:
        config = get_config()

    click.echo("🔍 Validating Configuration")
    click.echo("=" * 30)

    results = config.validate_config()

    if results["valid"]:
        click.echo("✅ Configuration is valid!")
    else:
        click.echo("❌ Configuration has errors!")

    if results["errors"]:
        click.echo("\n🚨 Errors:")
        for error in results["errors"]:
            click.echo(f"  • {error}")

    if results["warnings"]:
        click.echo("\n⚠️  Warnings:")
        for warning in results["warnings"]:
            click.echo(f"  • {warning}")

    if results["providers"]:
        click.echo("\n📋 Provider Validation:")
        for name, provider_results in results["providers"].items():
            status_icon = "✅" if provider_results["valid"] else "❌"
            click.echo(f"  {status_icon} {name}")

            if provider_results["errors"]:
                for error in provider_results["errors"]:
                    click.echo(f"    • Error: {error}")

            if provider_results["warnings"]:
                for warning in provider_results["warnings"]:
                    click.echo(f"    • Warning: {warning}")


@cli.command()
@click.option("--config-file", "-c", help="Configuration file path")
def test(config_file: Optional[str]):
    """Test provider availability."""
    if config_file:
        reset_config()
        from agents.core.external_api_config import ExternalAPIConfig

        config = ExternalAPIConfig(config_file)
    else:
        config = get_config()

    async def test_providers():
        click.echo("🧪 Testing Provider Availability")
        click.echo("=" * 35)

        config_manager = get_config()
        providers_info = {}

        # Check local models
        providers_info["local"] = {
            "available": True,
            "models": ["starcoder", "mistral", "qwen", "tinyllama"],
        }

        # Check external providers
        for provider_name, provider_config in config_manager.providers.items():
            if provider_config.enabled:
                try:
                    adapter = ModelProviderFactory.create_external_adapter(
                        provider_name
                    )
                    is_available = await adapter.check_availability()
                    providers_info[provider_name] = {
                        "available": is_available,
                        "provider_type": provider_config.provider_type.value,
                        "model": provider_config.model,
                        "timeout": provider_config.timeout,
                    }
                except Exception as e:
                    providers_info[provider_name] = {
                        "available": False,
                        "error": str(e),
                    }

        for provider_name, info in providers_info.items():
            if info.get("available"):
                click.echo(f"✅ {provider_name}: Available")
                if "provider_type" in info:
                    click.echo(f"   Type: {info['provider_type']}")
                if "model" in info:
                    click.echo(f"   Model: {info['model']}")
            else:
                click.echo(f"❌ {provider_name}: Unavailable")
                if "error" in info:
                    click.echo(f"   Error: {info['error']}")
            click.echo()

    asyncio.run(test_providers())


@cli.command()
@click.argument("name")
@click.argument("provider_type", type=click.Choice(["chatgpt", "claude", "chadgpt"]))
@click.argument("api_key")
@click.option(
    "--model",
    default=None,
    help="Model name (for chadgpt: gpt-5, gpt-5-mini, gpt-5-nano, claude-4.1-opus, claude-4.5-sonnet)",
)
@click.option("--timeout", default=60.0, help="Request timeout")
@click.option("--max-tokens", default=4000, help="Maximum tokens")
@click.option("--temperature", default=0.7, help="Temperature")
@click.option("--enabled/--disabled", default=True, help="Enable/disable provider")
@click.option("--config-file", "-c", help="Configuration file path")
def add(
    name: str,
    provider_type: str,
    api_key: str,
    model: Optional[str],
    timeout: float,
    max_tokens: int,
    temperature: float,
    enabled: bool,
    config_file: Optional[str],
):
    """Add a new provider."""
    if config_file:
        reset_config()
        from agents.core.external_api_config import ExternalAPIConfig

        config = ExternalAPIConfig(config_file)
    else:
        config = get_config()

    # Set default models if not specified
    if not model:
        if provider_type == "chatgpt":
            model = "gpt-3.5-turbo"
        elif provider_type == "claude":
            model = "claude-3-sonnet-20240229"

    provider_config = ProviderConfig(
        provider_type=ProviderType(provider_type),
        api_key=api_key,
        model=model,
        timeout=timeout,
        enabled=enabled,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    config.add_provider(name, provider_config)
    config.save_config()

    click.echo(f"✅ Added provider '{name}' ({provider_type})")


@cli.command()
@click.argument("name")
@click.option("--config-file", "-c", help="Configuration file path")
def remove(name: str, config_file: Optional[str]):
    """Remove a provider."""
    if config_file:
        reset_config()
        from agents.core.external_api_config import ExternalAPIConfig

        config = ExternalAPIConfig(config_file)
    else:
        config = get_config()

    if config.remove_provider(name):
        config.save_config()
        click.echo(f"✅ Removed provider '{name}'")
    else:
        click.echo(f"❌ Provider '{name}' not found")


@cli.command()
@click.argument("name")
@click.option("--config-file", "-c", help="Configuration file path")
def enable(name: str, config_file: Optional[str]):
    """Enable a provider."""
    if config_file:
        reset_config()
        from agents.core.external_api_config import ExternalAPIConfig

        config = ExternalAPIConfig(config_file)
    else:
        config = get_config()

    provider_config = config.get_provider(name)
    if provider_config:
        provider_config.enabled = True
        config.save_config()
        click.echo(f"✅ Enabled provider '{name}'")
    else:
        click.echo(f"❌ Provider '{name}' not found")


@cli.command()
@click.argument("name")
@click.option("--config-file", "-c", help="Configuration file path")
def disable(name: str, config_file: Optional[str]):
    """Disable a provider."""
    if config_file:
        reset_config()
        from agents.core.external_api_config import ExternalAPIConfig

        config = ExternalAPIConfig(config_file)
    else:
        config = get_config()

    provider_config = config.get_provider(name)
    if provider_config:
        provider_config.enabled = False
        config.save_config()
        click.echo(f"✅ Disabled provider '{name}'")
    else:
        click.echo(f"❌ Provider '{name}' not found")


@cli.command()
@click.argument("name")
@click.option("--config-file", "-c", help="Configuration file path")
def set_default(name: str, config_file: Optional[str]):
    """Set default provider."""
    if config_file:
        reset_config()
        from agents.core.external_api_config import ExternalAPIConfig

        config = ExternalAPIConfig(config_file)
    else:
        config = get_config()

    if config.set_default_provider(name):
        config.save_config()
        click.echo(f"✅ Set default provider to '{name}'")
    else:
        click.echo(f"❌ Provider '{name}' not found")


@cli.command()
@click.option("--config-file", "-c", help="Configuration file path")
def export(config_file: Optional[str]):
    """Export configuration to JSON."""
    if config_file:
        reset_config()
        from agents.core.external_api_config import ExternalAPIConfig

        config = ExternalAPIConfig(config_file)
    else:
        config = get_config()

    export_data = {
        "providers": {
            name: provider.to_dict() for name, provider in config.providers.items()
        },
        "default_provider": config.default_provider,
    }

    click.echo(json.dumps(export_data, indent=2))


@cli.command()
@click.argument("task_description")
@click.option("--language", default="python", help="Programming language")
@click.option("--prefer-speed", is_flag=True, help="Prefer faster models")
@click.option("--prefer-quality", is_flag=True, help="Prefer higher quality models")
@click.option("--show-all", is_flag=True, help="Show all model recommendations")
def recommend(
    task_description: str,
    language: str,
    prefer_speed: bool,
    prefer_quality: bool,
    show_all: bool,
):
    """Get smart model recommendation for a task."""
    click.echo("🧠 Smart Model Recommendation")
    click.echo("=" * 35)

    selector = get_smart_selector()

    click.echo(f"📝 Task: {task_description}")
    click.echo(f"🔤 Language: {language}")

    if prefer_speed:
        click.echo("⚡ Preference: Speed")
    elif prefer_quality:
        click.echo("🎯 Preference: Quality")
    else:
        click.echo("⚖️  Preference: Balanced")

    click.echo()

    # Get recommendation
    recommendation = selector.recommend_model(
        task_description, language, prefer_speed, prefer_quality
    )

    click.echo("🎯 Recommended Model:")
    click.echo(f"   Model: {recommendation.model}")
    click.echo(f"   Confidence: {recommendation.confidence:.2f}")
    click.echo(f"   Max tokens: {recommendation.max_tokens}")
    click.echo(f"   Temperature: {recommendation.temperature}")
    click.echo(f"   Reasoning: {recommendation.reasoning}")

    if show_all:
        click.echo("\n📈 All Model Recommendations:")
        all_recommendations = selector.get_all_recommendations(
            task_description, language
        )

        for i, rec in enumerate(all_recommendations, 1):
            status = "✅" if rec.model == recommendation.model else "  "
            click.echo(f"   {status} {i}. {rec.model}: {rec.confidence:.2f}")
            click.echo(f"      {rec.reasoning}")


@cli.command()
def models():
    """Show all available models and their capabilities."""
    click.echo("🤖 Available Models")
    click.echo("=" * 20)

    selector = get_smart_selector()
    capabilities = selector.get_model_capabilities()

    for model, info in capabilities.items():
        click.echo(f"\n🔧 {model}:")
        click.echo(f"   Display: {info['display_name']}")
        click.echo(f"   Description: {info['description']}")
        click.echo(f"   Max tokens: {info['max_tokens']}")
        click.echo(f"   Temperature: {info['temperature']}")
        click.echo(f"   Speed: {info['speed']}")
        click.echo(f"   Cost: {info['cost']}")
        click.echo(f"   Best for: {', '.join([t.value for t in info['best_for']])}")
        click.echo(f"   Complexity: {', '.join([c.value for c in info['complexity']])}")


@cli.command()
@click.argument("input_file", type=click.File("r"))
@click.option("--output-file", "-o", help="Output configuration file")
def import_config(input_file, output_file: Optional[str]):
    """Import configuration from JSON file."""
    try:
        data = json.load(input_file)

        # Create new config instance
        from agents.core.external_api_config import ExternalAPIConfig

        config = ExternalAPIConfig()

        # Load from imported data
        config._load_from_dict(data)

        # Save to file
        if output_file:
            config.config_file = output_file
        config.save_config()

        click.echo(f"✅ Imported configuration to {config.config_file}")

    except Exception as e:
        click.echo(f"❌ Failed to import configuration: {e}")


if __name__ == "__main__":
    cli()
