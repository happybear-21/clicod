"""
clicod - CLI Code Generator using Gemini AI
A command-line tool for generating Perl scripts with AI assistance
"""

import os
import sys
import json
import click
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from pathlib import Path
import getpass

console = Console()

class ClicodConfig:
    """Configuration management for clicod"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.clicod'
        self.config_file = self.config_dir / 'config.json'
        self.config_dir.mkdir(exist_ok=True)
        self.config = self._load_config()
    
    def _load_config(self):
        """Load configuration from file"""
        default_config = {
            'gemini_api_key': None,
            'default_model': 'gemini-2.5-flash',
            'save_location': str(Path.cwd()),
            'auto_save': False,
            'streaming': False
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                    default_config.update(saved_config)
            except (json.JSONDecodeError, FileNotFoundError):
                console.print("⚠️ [yellow]Config file corrupted, using defaults[/yellow]")
        
        return default_config
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            console.print(f"❌ [red]Error saving config: {str(e)}[/red]")
            return False
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value"""
        self.config[key] = value
    
    def get_api_key(self):
        """Get API key with fallback to environment"""
        # Priority: config file -> environment variable -> prompt user
        api_key = self.get('gemini_api_key')
        if not api_key:
            api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            console.print("🔐 [yellow]Gemini API key not found in configuration[/yellow]")
            if Confirm.ask("Would you like to set it now?"):
                api_key = getpass.getpass("Enter your Gemini API key: ")
                if api_key:
                    self.set('gemini_api_key', api_key)
                    self.save_config()
                    console.print("✅ [green]API key saved to clicod config[/green]")
        return api_key

class ClicodGenerator:
    def __init__(self, model_name=None, config=None):
        self.config = config or ClicodConfig()
        
        # Get API key from configuration
        self.api_key = self.config.get_api_key()
        
        if not self.api_key:
            console.print("❌ [red]Error: No Gemini API key configured![/red]")
            console.print("Run: clicod config --set-key")
            sys.exit(1)
        
        try:
            # Import and configure the Google Gen AI SDK
            from google import genai
            
            # Initialize the client with the API key
            self.client = genai.Client(api_key=self.api_key)
            
            # Use model from parameter, config, or default
            self.model_name = model_name or self.config.get('default_model', 'gemini-2.5-flash')
            
            console.print(f"✅ [green]clicod using model: {self.model_name}[/green]")
        except ImportError:
            console.print("❌ [red]Error: google-genai SDK not found![/red]")
            console.print("Install with: pip install google-genai")
            sys.exit(1)
        except Exception as e:
            console.print(f"❌ [red]Error configuring Gemini API: {str(e)}[/red]")
            sys.exit(1)
        
        # Enhanced system prompt for Perl code generation
        self.system_prompt = """
You are an expert Perl programmer. Generate high-quality, production-ready Perl code with:

1. Modern Perl practices (use strict; use warnings;)
2. Proper variable scoping and error handling
3. Clear documentation and comments
4. CPAN module recommendations when appropriate
5. Complete executable scripts with examples

Always wrap Perl code in ```
code here
```

Focus on backend development, system automation, and data processing tasks.
"""

    def generate_code(self, prompt, save_to_file=None, filename=None):
        try:
            # Use config defaults if not specified
            if save_to_file is None:
                save_to_file = self.config.get('auto_save', False)
            
            # Prepare the enhanced prompt
            enhanced_prompt = f"""
{self.system_prompt}

User Request: {prompt}

Please provide:
1. Complete Perl script with proper shebang and pragmas
2. Required CPAN modules (if any)
3. Usage examples
4. Brief explanation of the approach

Generate clean, well-documented Perl code following modern best practices.
"""
            
            console.print(f"🤖 [yellow]clicod generating code using {self.model_name}...[/yellow]")
            
            # Use the new SDK method with proper parameters
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=enhanced_prompt,
                config={
                    'temperature': 0.1,
                    'top_p': 0.8,
                    'top_k': 20,
                    'max_output_tokens': 4000,
                }
            )
            
            if response.text:
                # Display the response with rich formatting
                console.print("\n" + "="*60)
                console.print(Panel(Markdown(response.text), title=f"clicod Generated Code ({self.model_name})", border_style="green"))
                
                # Extract Perl code blocks
                perl_code = self._extract_code_blocks(response.text)
                cpan_modules = self._extract_cpan_modules(response.text)
                
                if perl_code and save_to_file:
                    self._save_code_to_file(perl_code, filename, cpan_modules)
                
                return response.text, perl_code, cpan_modules
            else:
                console.print("❌ [red]No response generated from Gemini[/red]")
                return None, None, None
                
        except Exception as e:
            console.print(f"❌ [red]Error generating code: {str(e)}[/red]")
            return None, None, None

    def _extract_code_blocks(self, text):
        """Extract Perl code from markdown code blocks"""
        import re
        
        # Look for ```
        perl_blocks = re.findall(r'``````', text, re.DOTALL)
        if perl_blocks:
            return '\n\n'.join(perl_blocks)
        
        # Fallback to any code blocks
        code_blocks = re.findall(r'``````', text, re.DOTALL)
        if code_blocks:
            return '\n\n'.join(code_blocks)
        
        return None

    def _extract_cpan_modules(self, text):
        """Extract CPAN module installation commands"""
        import re
        
        modules = []
        # Look for cpan install commands
        cpan_matches = re.findall(r'cpan install ([A-Za-z0-9::_\-\s]+)', text, re.IGNORECASE)
        modules.extend(cpan_matches)
        
        # Look for use Module::Name statements
        use_matches = re.findall(r'use\s+([A-Za-z0-9::_]+)', text)
        modules.extend([m for m in use_matches if '::' in m and m not in ['strict', 'warnings']])
        
        return list(set(modules))  # Remove duplicates

    def _save_code_to_file(self, code, filename=None, cpan_modules=None):
        """Save generated code to a file with CPAN modules info"""
        save_location = Path(self.config.get('save_location', Path.cwd()))
        
        if not filename:
            filename = Prompt.ask("Enter filename", default="clicod_generated.pl")
        
        if not filename.endswith('.pl'):
            filename += '.pl'
        
        filepath = save_location / filename
        
        try:
            with open(filepath, 'w') as f:
                f.write("#!/usr/bin/env perl\n")
                f.write("# Generated by clicod - CLI Code Generator\n")
                f.write(f"# Model: {self.model_name}\n")
                f.write("# https://github.com/yourusername/clicod\n")
                f.write("# " + "="*50 + "\n")
                
                if cpan_modules:
                    f.write("#\n# Required CPAN modules:\n")
                    for module in cpan_modules:
                        f.write(f"# cpan install {module}\n")
                    f.write("#\n")
                
                f.write("\n")
                f.write(code)
            
            # Make file executable on Unix systems
            try:
                os.chmod(filepath, 0o755)
            except:
                pass  # Skip on Windows
            
            console.print(f"✅ [green]Code saved to {filepath}[/green]")
            
            if cpan_modules:
                console.print(f"📦 [blue]Required modules: {', '.join(cpan_modules)}[/blue]")
            
            console.print(f"🏃 [blue]Run with: perl {filepath}[/blue]")
            
        except Exception as e:
            console.print(f"❌ [red]Error saving file: {str(e)}[/red]")

    def stream_generate(self, prompt):
        """Generate code with streaming response"""
        try:
            enhanced_prompt = f"{self.system_prompt}\n\nUser Request: {prompt}"
            
            console.print(f"🤖 [yellow]clicod streaming from {self.model_name}...[/yellow]")
            
            response = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=enhanced_prompt
            )
            
            full_text = ""
            for chunk in response:
                if chunk.text:
                    console.print(chunk.text, end="")
                    full_text += chunk.text
            
            return full_text
        except Exception as e:
            console.print(f"❌ [red]Error streaming code: {str(e)}[/red]")
            return None

# CLI Commands
@click.group()
@click.version_option(version='1.0.0', prog_name='clicod')
@click.option('--model', '-m', help='Specify Gemini model to use')
@click.pass_context
def cli(ctx, model):
    """
    🚀 clicod - CLI Code Generator
    
    Generate Perl scripts using Gemini AI with natural language descriptions.
    Configuration is stored in ~/.clicod/config.json
    """
    ctx.ensure_object(dict)
    ctx.obj['config'] = ClicodConfig()
    ctx.obj['generator'] = ClicodGenerator(model, ctx.obj['config'])

@cli.command()
@click.argument('prompt', nargs=-1, required=False)
@click.option('--save', '-s', is_flag=True, help='Save generated code to file')
@click.option('--filename', '-f', help='Specify output filename')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode')
@click.option('--stream', is_flag=True, help='Stream response in real-time')
def generate(prompt, save, filename, interactive, stream):
    """Generate Perl code based on natural language description"""
    generator = click.get_current_context().obj['generator']
    config = click.get_current_context().obj['config']
    
    # Use config defaults for streaming if not specified
    if not stream:
        stream = config.get('streaming', False)
    
    if interactive:
        console.print("🚀 [bold blue]clicod - Interactive Code Generation[/bold blue]")
        console.print(f"Using model: [green]{generator.model_name}[/green]")
        console.print("Commands: 'exit', 'quit', 'config', 'save on/off', 'stream on/off'\n")
        
        try:
            while True:
                user_input = Prompt.ask(f"\n[bold cyan]📝 Describe your Perl script[/bold cyan]")
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    console.print("👋 [yellow]Thanks for using clicod![/yellow]")
                    break
                
                if user_input.lower() == 'config':
                    _show_current_config(config)
                    continue
                
                if user_input.lower().startswith('save '):
                    setting = user_input.split(' ', 1).lower()
                    if setting in ['on', 'true', 'yes']:
                        config.set('auto_save', True)
                        config.save_config()
                        console.print("✅ [green]Auto-save enabled[/green]")
                    elif setting in ['off', 'false', 'no']:
                        config.set('auto_save', False)
                        config.save_config()
                        console.print("✅ [green]Auto-save disabled[/green]")
                    continue
                
                if user_input.lower().startswith('stream '):
                    setting = user_input.split(' ', 1).lower()
                    if setting in ['on', 'true', 'yes']:
                        stream = True
                        console.print("✅ [green]Streaming enabled for this session[/green]")
                    elif setting in ['off', 'false', 'no']:
                        stream = False
                        console.print("✅ [green]Streaming disabled for this session[/green]")
                    continue
                
                if stream:
                    full_response = generator.stream_generate(user_input)
                    if full_response:
                        code = generator._extract_code_blocks(full_response)
                        modules = generator._extract_cpan_modules(full_response)
                        if code and (config.get('auto_save') or Confirm.ask("\n💾 Save this code to file?")):
                            save_filename = Prompt.ask("Enter filename", default="clicod_script.pl")
                            generator._save_code_to_file(code, save_filename, modules)
                else:
                    response, code, modules = generator.generate_code(user_input, save)
                    if code and not config.get('auto_save') and Confirm.ask("\n💾 Save this code to file?"):
                        save_filename = Prompt.ask("Enter filename", default="clicod_script.pl")
                        generator._save_code_to_file(code, save_filename, modules)
                    
        except KeyboardInterrupt:
            console.print("\n👋 [yellow]Thanks for using clicod![/yellow]")
    else:
        if not prompt:
            console.print("❌ [red]Please provide a description or use --interactive mode[/red]")
            console.print("Example: clicod generate 'Create a CSV parser script'")
            return
        
        prompt_text = ' '.join(prompt)
        
        if stream:
            full_response = generator.stream_generate(prompt_text)
            if full_response and save:
                code = generator._extract_code_blocks(full_response)
                modules = generator._extract_cpan_modules(full_response)
                generator._save_code_to_file(code, filename, modules)
        else:
            response, code, modules = generator.generate_code(prompt_text, save, filename)

@cli.command()
@click.option('--set-key', is_flag=True, help='Set Gemini API key')
@click.option('--set-model', help='Set default model')
@click.option('--set-save-location', help='Set default save location')
@click.option('--auto-save', type=bool, help='Enable/disable auto-save')
@click.option('--streaming', type=bool, help='Enable/disable streaming by default')
@click.option('--show', is_flag=True, help='Show current configuration')
@click.option('--reset', is_flag=True, help='Reset configuration to defaults')
def config(set_key, set_model, set_save_location, auto_save, streaming, show, reset):
    """Configure clicod settings"""
    config = click.get_current_context().obj['config']
    
    if reset:
        if Confirm.ask("⚠️ Reset all configuration to defaults?"):
            config.config_file.unlink(missing_ok=True)
            console.print("✅ [green]Configuration reset to defaults[/green]")
        return
    
    if set_key:
        api_key = getpass.getpass("Enter your Gemini API key: ")
        if api_key:
            config.set('gemini_api_key', api_key)
            config.save_config()
            console.print("✅ [green]API key updated[/green]")
    
    if set_model:
        config.set('default_model', set_model)
        config.save_config()
        console.print(f"✅ [green]Default model set to: {set_model}[/green]")
    
    if set_save_location:
        save_path = Path(set_save_location).expanduser().resolve()
        if save_path.exists():
            config.set('save_location', str(save_path))
            config.save_config()
            console.print(f"✅ [green]Save location set to: {save_path}[/green]")
        else:
            console.print(f"❌ [red]Directory does not exist: {save_path}[/red]")
    
    if auto_save is not None:
        config.set('auto_save', auto_save)
        config.save_config()
        console.print(f"✅ [green]Auto-save {'enabled' if auto_save else 'disabled'}[/green]")
    
    if streaming is not None:
        config.set('streaming', streaming)
        config.save_config()
        console.print(f"✅ [green]Streaming {'enabled' if streaming else 'disabled'}[/green]")
    
    if show or not any([set_key, set_model, set_save_location, auto_save is not None, streaming is not None]):
        _show_current_config(config)

def _show_current_config(config):
    """Display current configuration"""
    table = Table(title="clicod Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    api_key = config.get('gemini_api_key')
    masked_key = f"{api_key[:8]}...{api_key[-4:]}" if api_key else "Not set"
    
    table.add_row("API Key", masked_key)
    table.add_row("Default Model", config.get('default_model', 'gemini-2.5-flash'))
    table.add_row("Save Location", config.get('save_location', str(Path.cwd())))
    table.add_row("Auto Save", str(config.get('auto_save', False)))
    table.add_row("Streaming", str(config.get('streaming', False)))
    table.add_row("Config File", str(config.config_file))
    
    console.print(table)

@cli.command()
def test():
    """Test Gemini API connection"""
    generator = click.get_current_context().obj['generator']
    console.print(f"🔌 [blue]Testing clicod connection with {generator.model_name}...[/blue]")
    
    try:
        test_response = generator.client.models.generate_content(
            model=generator.model_name,
            contents="Generate a simple Perl hello world script"
        )
        if test_response.text:
            console.print("✅ [green]Connection successful![/green]")
        else:
            console.print("❌ [red]Connection failed - no response[/red]")
    except Exception as e:
        console.print(f"❌ [red]Connection failed: {str(e)}[/red]")

@cli.command()
def examples():
    """Show clicod usage examples"""
    examples_text = """
## 🚀 clicod Usage Examples

### First Time Setup:
```bash
clicod config --set-key  # Set your Gemini API key
clicod config --show     # View current configuration
```

### Basic Usage:
```bash
clicod generate "Create a CSV parser with error handling"
clicod generate "Build a log file analyzer" --save
clicod generate "Simple web scraper" --stream
```

### Configuration:
```bash
clicod config --set-model gemini-2.5-pro
clicod config --auto-save true
clicod config --set-save-location ~/scripts
```

### Interactive Mode:
```bash
clicod generate --interactive
# Commands in interactive mode:
# - save on/off
# - stream on/off  
# - config
# - exit/quit
```

### Example Prompts:
- "Create a Perl script to monitor disk usage and send alerts"
- "Build a JSON parser with validation and error handling"
- "Generate a simple HTTP client with authentication"
- "Create a log rotation script for system administration"
"""
    console.print(Panel(examples_text, title="clicod Examples", border_style="blue"))

@cli.command()
def about():
    """About clicod"""
    config = click.get_current_context().obj['config']
    
    about_text = f"""
## 🚀 clicod - CLI Code Generator

**Version:** 1.0.0  
**Configuration:** {config.config_file}

**Configuration stored in:** `{config.config_file}`
"""
    console.print(Panel(about_text, title="About clicod", border_style="cyan"))

if __name__ == '__main__':
    cli()