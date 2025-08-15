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
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.syntax import Syntax
from pathlib import Path
import getpass

# Enhanced system prompt with detailed JSON format instructions
SYSTEM_PROMPT = """
You are an expert Perl programmer. Generate high-quality, production-ready Perl code with modern practices.

CRITICAL: You MUST respond in valid JSON format with the following exact structure:

{
  "status": "success" | "error",
  "response_type": "perl_code_generation",
  "metadata": {
    "model_used": "your_model_name",
    "timestamp": "current_time",
    "complexity_level": "beginner" | "intermediate" | "advanced",
    "estimated_lines": number
  },
  "perl_code": {
    "main_script": "complete perl script with shebang and all code",
    "additional_files": [
      {
        "filename": "optional_additional_file.pl",
        "content": "file content",
        "description": "what this file does"
      }
    ]
  },
  "dependencies": {
    "core_modules": ["List::Util", "File::Spec"],
    "cpan_modules": [
      {
        "name": "Module::Name",
        "install_command": "cpan install Module::Name",
        "purpose": "what this module does"
      }
    ],
    "system_requirements": ["perl 5.10+", "additional requirements"]
  },
  "documentation": {
    "description": "Brief description of what the script does",
    "usage_examples": [
      "perl script.pl --help",
      "perl script.pl input.txt output.txt"
    ],
    "features": ["feature 1", "feature 2"],
    "notes": ["important note 1", "important note 2"]
  },
  "code_structure": {
    "functions": [
      {
        "name": "function_name",
        "description": "what it does",
        "parameters": ["param1", "param2"]
      }
    ],
    "main_sections": [
      "Configuration",
      "Main Logic", 
      "Helper Functions",
      "Error Handling"
    ]
  },
  "best_practices": [
    "Modern Perl practices used",
    "Error handling implemented",
    "Code documentation included"
  ],
  "testing": {
    "test_cases": [
      "test case 1 description",
      "test case 2 description"
    ],
    "sample_input": "example input data",
    "expected_output": "example output"
  }
}

IMPORTANT RULES:
1. ALWAYS return valid JSON - no markdown, no code blocks, just pure JSON
2. Include complete, executable Perl code in the "main_script" field
3. Use proper escaping for quotes and newlines in JSON strings
4. Include comprehensive error handling in your Perl code
5. Follow modern Perl best practices (use strict; use warnings;)
6. Provide clear, detailed documentation
7. If the request is unclear, still provide a valid JSON response with appropriate error status

Example of proper JSON escaping for Perl code:
"main_script": "#!/usr/bin/env perl\\nuse strict;\\nuse warnings;\\n\\nprint \\"Hello World\\\\n\\";"

Remember: Your entire response must be parseable as JSON. No explanatory text outside the JSON structure.
"""

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
            'streaming': False,
            'json_format': True
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
        
        self.api_key = self.config.get_api_key()
        
        if not self.api_key:
            console.print("❌ [red]Error: No Gemini API key configured![/red]")
            console.print("Run: clicod config --set-key")
            sys.exit(1)
        
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.model_name = model_name or self.config.get('default_model', 'gemini-2.5-flash')
            console.print(f"✅ [green]clicod using model: {self.model_name}[/green]")
        except ImportError:
            console.print("❌ [red]Error: google-genai SDK not found![/red]")
            console.print("Install with: pip install google-genai")
            sys.exit(1)
        except Exception as e:
            console.print(f"❌ [red]Error configuring Gemini API: {str(e)}[/red]")
            sys.exit(1)
        
        self.system_prompt = SYSTEM_PROMPT

    def generate_code(self, prompt, save_to_file=None, filename=None):
        """Generate code with structured JSON response"""
        try:
            if save_to_file is None:
                save_to_file = self.config.get('auto_save', False)
            
            enhanced_prompt = f"""
{self.system_prompt}

User Request: {prompt}

Remember: Respond ONLY with valid JSON following the exact structure specified above. 
Include complete, executable Perl code with proper escaping in the JSON response.
"""
            
            console.print(f"🤖 [yellow]clicod generating structured code using {self.model_name}...[/yellow]")
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=enhanced_prompt,
                config={
                    'temperature': 0.1,
                    'top_p': 0.8,
                    'top_k': 20,
                    'max_output_tokens': 6000,
                }
            )
            
            if response.text:
                # Parse the JSON response
                parsed_response = self._parse_json_response(response.text)
                
                if parsed_response:
                    self._render_structured_output(parsed_response)
                    
                    # Extract Perl code from JSON structure
                    perl_code = parsed_response.get('perl_code', {}).get('main_script', '')
                    dependencies = parsed_response.get('dependencies', {})
                    
                    if perl_code and save_to_file:
                        self._save_structured_code(parsed_response, filename)
                    
                    return parsed_response, perl_code, dependencies
                else:
                    console.print("❌ [red]Failed to parse JSON response from model[/red]")
                    # Fallback to displaying raw response
                    console.print(Panel(response.text, title="Raw Response (JSON Parse Failed)", border_style="red"))
                    return None, None, None
            else:
                console.print("❌ [red]No response generated from Gemini[/red]")
                return None, None, None
                
        except Exception as e:
            console.print(f"❌ [red]Error generating code: {str(e)}[/red]")
            return None, None, None

    def _parse_json_response(self, response_text):
        """Parse JSON response with error handling"""
        try:
            # Clean the response text
            cleaned_text = response_text.strip()
            
            # Try to find JSON content if wrapped in markdown
            if '```' in cleaned_text and 'json' in cleaned_text:
                start = cleaned_text.find('```json') + 7
                end = cleaned_text.find('```', start)
                if end != -1:
                    cleaned_text = cleaned_text[start:end].strip()
            elif '```' in cleaned_text:
                start = cleaned_text.find('```') + 3
                end = cleaned_text.rfind('```')
                if end != -1 and end > start:
                    cleaned_text = cleaned_text[start:end].strip()
            
            # Parse JSON
            parsed = json.loads(cleaned_text)
            return parsed
            
        except json.JSONDecodeError as e:
            console.print(f"❌ [red]JSON parsing error: {str(e)}[/red]")
            console.print(f"🔍 [yellow]Response preview: {response_text[:200]}...[/yellow]")
            return None
        except Exception as e:
            console.print(f"❌ [red]Error processing response: {str(e)}[/red]")
            return None

    def _render_structured_output(self, parsed_response):
        """Render the structured JSON response with rich formatting"""
        console.print("\n" + "="*80)
        
        # Status and metadata
        status = parsed_response.get('status', 'unknown')
        metadata = parsed_response.get('metadata', {})
        
        status_color = "green" if status == "success" else "red"
        console.print(f"📊 [bold {status_color}]Status: {status.upper()}[/bold {status_color}]")
        
        if metadata:
            console.print(f"🔧 [blue]Complexity: {metadata.get('complexity_level', 'N/A')} | "
                        f"Estimated Lines: {metadata.get('estimated_lines', 'N/A')}[/blue]")
        
        # Description and features
        documentation = parsed_response.get('documentation', {})
        if documentation.get('description'):
            console.print(Panel(
                documentation['description'], 
                title="📝 Description", 
                border_style="cyan"
            ))
        
        # Perl code display
        perl_code_section = parsed_response.get('perl_code', {})
        main_script = perl_code_section.get('main_script', '')
        
        if main_script:
            console.print(Panel(
                Syntax(main_script, "perl", theme="monokai", line_numbers=True),
                title="🐪 Generated Perl Script",
                border_style="green"
            ))
        
        # Additional files
        additional_files = perl_code_section.get('additional_files', [])
        if additional_files:
            for file_info in additional_files:
                console.print(Panel(
                    Syntax(file_info.get('content', ''), "perl", theme="monokai"),
                    title=f"📄 {file_info.get('filename', 'Additional File')} - {file_info.get('description', '')}",
                    border_style="blue"
                ))
        
        # Dependencies
        dependencies = parsed_response.get('dependencies', {})
        if dependencies:
            self._render_dependencies(dependencies)
        
        # Code structure
        code_structure = parsed_response.get('code_structure', {})
        if code_structure:
            self._render_code_structure(code_structure)
        
        # Usage examples
        usage_examples = documentation.get('usage_examples', [])
        if usage_examples:
            examples_text = "\n".join([f"• {example}" for example in usage_examples])
            console.print(Panel(
                examples_text,
                title="🚀 Usage Examples",
                border_style="yellow"
            ))
        
        # Testing information
        testing = parsed_response.get('testing', {})
        if testing:
            self._render_testing_info(testing)
        
        # Best practices
        best_practices = parsed_response.get('best_practices', [])
        if best_practices:
            practices_text = "\n".join([f"✓ {practice}" for practice in best_practices])
            console.print(Panel(
                practices_text,
                title="✨ Best Practices Applied",
                border_style="green"
            ))

    def _render_dependencies(self, dependencies):
        """Render dependencies section"""
        table = Table(title="📦 Dependencies")
        table.add_column("Type", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Install Command", style="yellow")
        table.add_column("Purpose", style="blue")
        
        # Core modules
        core_modules = dependencies.get('core_modules', [])
        for module in core_modules:
            table.add_row("Core", module, "Built-in", "Perl core module")
        
        # CPAN modules
        cpan_modules = dependencies.get('cpan_modules', [])
        for module_info in cpan_modules:
            if isinstance(module_info, dict):
                table.add_row(
                    "CPAN",
                    module_info.get('name', ''),
                    module_info.get('install_command', ''),
                    module_info.get('purpose', '')
                )
            else:
                table.add_row("CPAN", str(module_info), f"cpan install {module_info}", "")
        
        # System requirements
        system_reqs = dependencies.get('system_requirements', [])
        for req in system_reqs:
            table.add_row("System", req, "See documentation", "System requirement")
        
        if table.rows:
            console.print(table)

    def _render_code_structure(self, code_structure):
        """Render code structure information"""
        functions = code_structure.get('functions', [])
        if functions:
            func_table = Table(title="🔧 Functions")
            func_table.add_column("Function", style="cyan")
            func_table.add_column("Description", style="green")
            func_table.add_column("Parameters", style="yellow")
            
            for func in functions:
                if isinstance(func, dict):
                    params = ", ".join(func.get('parameters', []))
                    func_table.add_row(
                        func.get('name', ''),
                        func.get('description', ''),
                        params
                    )
            
            console.print(func_table)
        
        main_sections = code_structure.get('main_sections', [])
        if main_sections:
            sections_text = "\n".join([f"• {section}" for section in main_sections])
            console.print(Panel(
                sections_text,
                title="🏗️ Code Structure",
                border_style="blue"
            ))

    def _render_testing_info(self, testing):
        """Render testing information"""
        test_cases = testing.get('test_cases', [])
        sample_input = testing.get('sample_input', '')
        expected_output = testing.get('expected_output', '')
        
        if test_cases or sample_input or expected_output:
            testing_content = ""
            
            if test_cases:
                testing_content += "Test Cases:\n"
                testing_content += "\n".join([f"• {case}" for case in test_cases])
                testing_content += "\n\n"
            
            if sample_input:
                testing_content += f"Sample Input:\n{sample_input}\n\n"
            
            if expected_output:
                testing_content += f"Expected Output:\n{expected_output}"
            
            console.print(Panel(
                testing_content.strip(),
                title="🧪 Testing Information",
                border_style="magenta"
            ))

    def _save_structured_code(self, parsed_response, filename=None):
        """Save generated code with comprehensive metadata"""
        save_location = Path(self.config.get('save_location', Path.cwd()))
        
        if not filename:
            filename = Prompt.ask("Enter filename", default="clicod_generated.pl")
        
        if not filename.endswith('.pl'):
            filename += '.pl'
        
        filepath = save_location / filename
        
        try:
            perl_code_section = parsed_response.get('perl_code', {})
            main_script = perl_code_section.get('main_script', '')
            dependencies = parsed_response.get('dependencies', {})
            documentation = parsed_response.get('documentation', {})
            
            with open(filepath, 'w') as f:
                # Header with metadata
                f.write("#!/usr/bin/env perl\n")
                f.write("# Generated by clicod - CLI Code Generator\n")
                f.write(f"# Model: {self.model_name}\n")
                f.write("# https://github.com/happybear-21/clicod\n")
                f.write("# " + "="*50 + "\n")
                
                # Description
                if documentation.get('description'):
                    f.write(f"# Description: {documentation['description']}\n")
                
                # Dependencies
                cpan_modules = dependencies.get('cpan_modules', [])
                if cpan_modules:
                    f.write("#\n# Required CPAN modules:\n")
                    for module in cpan_modules:
                        if isinstance(module, dict):
                            f.write(f"# {module.get('install_command', '')}\n")
                        else:
                            f.write(f"# cpan install {module}\n")
                
                # Usage examples
                usage_examples = documentation.get('usage_examples', [])
                if usage_examples:
                    f.write("#\n# Usage examples:\n")
                    for example in usage_examples:
                        f.write(f"# {example}\n")
                
                f.write("#\n" + "# " + "="*50 + "\n\n")
                
                # Main script content
                f.write(main_script)
            
            # Save additional files
            additional_files = perl_code_section.get('additional_files', [])
            for file_info in additional_files:
                add_filename = file_info.get('filename', 'additional.pl')
                add_filepath = save_location / add_filename
                with open(add_filepath, 'w') as f:
                    f.write(file_info.get('content', ''))
                console.print(f"✅ [green]Additional file saved: {add_filepath}[/green]")
            
            # Make file executable on Unix systems
            try:
                os.chmod(filepath, 0o755)
            except:
                pass
            
            console.print(f"✅ [green]Code saved to {filepath}[/green]")
            
            # Show dependency installation commands
            if cpan_modules:
                console.print("📦 [blue]Install dependencies with:[/blue]")
                for module in cpan_modules:
                    if isinstance(module, dict):
                        console.print(f"   {module.get('install_command', '')}")
            
            console.print(f"🏃 [blue]Run with: perl {filepath}[/blue]")
            
        except Exception as e:
            console.print(f"❌ [red]Error saving file: {str(e)}[/red]")

    def stream_generate(self, prompt):
        """Generate code with streaming response (JSON format)"""
        try:
            enhanced_prompt = f"{self.system_prompt}\n\nUser Request: {prompt}"
            
            console.print(f"🤖 [yellow]clicod streaming from {self.model_name}...[/yellow]")
            
            response = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=enhanced_prompt
            )
            
            full_text = ""
            console.print("📡 [blue]Streaming response...[/blue]\n")
            
            for chunk in response:
                if chunk.text:
                    console.print(chunk.text, end="")
                    full_text += chunk.text
            
            console.print("\n\n🔄 [yellow]Processing streamed JSON response...[/yellow]")
            
            # Parse and render the complete JSON response
            parsed_response = self._parse_json_response(full_text)
            if parsed_response:
                console.print("\n" + "="*80)
                console.print("📊 [bold green]Parsed Structured Response:[/bold green]")
                self._render_structured_output(parsed_response)
                return parsed_response
            
            return full_text
        except Exception as e:
            console.print(f"❌ [red]Error streaming code: {str(e)}[/red]")
            return None

# CLI Commands remain the same but with updated calls to the new methods
@click.group()
@click.version_option(version='1.0.0', prog_name='clicod')
@click.option('--model', '-m', help='Specify Gemini model to use')
@click.pass_context
def cli(ctx, model):
    """
    🚀 clicod - CLI Code Generator
    
    Generate Perl scripts using Gemini AI with structured JSON responses.
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
    
    if not stream:
        stream = config.get('streaming', False)
    
    if interactive:
        console.print("🚀 [bold blue]clicod - Interactive Structured Code Generation[/bold blue]")
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
                    setting = user_input.split(' ', 1)[1].lower()
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
                    setting = user_input.split(' ', 1)[1].lower()
                    if setting in ['on', 'true', 'yes']:
                        stream = True
                        console.print("✅ [green]Streaming enabled for this session[/green]")
                    elif setting in ['off', 'false', 'no']:
                        stream = False
                        console.print("✅ [green]Streaming disabled for this session[/green]")
                    continue
                
                if stream:
                    parsed_response = generator.stream_generate(user_input)
                    if parsed_response and isinstance(parsed_response, dict):
                        perl_code = parsed_response.get('perl_code', {}).get('main_script', '')
                        if perl_code and (config.get('auto_save') or Confirm.ask("\n💾 Save this code to file?")):
                            save_filename = Prompt.ask("Enter filename", default="clicod_script.pl")
                            generator._save_structured_code(parsed_response, save_filename)
                else:
                    parsed_response, perl_code, dependencies = generator.generate_code(user_input, save)
                    if parsed_response and not config.get('auto_save') and Confirm.ask("\n💾 Save this code to file?"):
                        save_filename = Prompt.ask("Enter filename", default="clicod_script.pl")
                        generator._save_structured_code(parsed_response, save_filename)
                    
        except KeyboardInterrupt:
            console.print("\n👋 [yellow]Thanks for using clicod![/yellow]")
    else:
        if not prompt:
            console.print("❌ [red]Please provide a description or use --interactive mode[/red]")
            console.print("Example: clicod generate 'Create a CSV parser script'")
            return
        
        prompt_text = ' '.join(prompt)
        
        if stream:
            parsed_response = generator.stream_generate(prompt_text)
            if parsed_response and isinstance(parsed_response, dict) and save:
                generator._save_structured_code(parsed_response, filename)
        else:
            parsed_response, perl_code, dependencies = generator.generate_code(prompt_text, save, filename)

# Keep all other CLI commands the same as they were in the original code
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
    table.add_row("JSON Format", str(config.get('json_format', True)))
    table.add_row("Config File", str(config.config_file))
    
    console.print(table)

@cli.command()
def test():
    """Test Gemini API connection with JSON format"""
    generator = click.get_current_context().obj['generator']
    console.print(f"🔌 [blue]Testing clicod connection with {generator.model_name} (JSON format)...[/blue]")
    
    try:
        test_prompt = f"""
{generator.system_prompt}

User Request: Generate a simple Perl hello world script

This is a test request. Please respond with the exact JSON format specified.
"""
        
        test_response = generator.client.models.generate_content(
            model=generator.model_name,
            contents=test_prompt
        )
        
        if test_response.text:
            parsed = generator._parse_json_response(test_response.text)
            if parsed:
                console.print("✅ [green]Connection and JSON parsing successful![/green]")
                console.print(f"📊 [blue]Response status: {parsed.get('status', 'unknown')}[/blue]")
            else:
                console.print("⚠️ [yellow]Connection successful but JSON parsing failed[/yellow]")
        else:
            console.print("❌ [red]Connection failed - no response[/red]")
    except Exception as e:
        console.print(f"❌ [red]Connection failed: {str(e)}[/red]")

@cli.command()
def examples():
    """Show clicod usage examples with JSON format"""
    examples_text = """
## 🚀 clicod Usage Examples (JSON Format)

### First Time Setup:
```
clicod config --set-key  # Set your Gemini API key
clicod config --show     # View current configuration
clicod test             # Test JSON format connection
```

### Basic Usage:
```
clicod generate "Create a CSV parser with error handling"
clicod generate "Build a log file analyzer" --save
clicod generate "Simple web scraper" --stream
```

### JSON Response Structure:
The AI now returns structured JSON with:
- Complete Perl code with proper escaping
- Detailed dependency information
- Usage examples and testing info
- Code structure documentation
- Best practices applied

### Interactive Mode:
```
clicod generate --interactive
# Enhanced with structured JSON responses
# Better dependency tracking
# Comprehensive code documentation
```

### Example Prompts:
- "Create a Perl script to monitor disk usage and send alerts"
- "Build a JSON parser with validation and error handling" 
- "Generate a simple HTTP client with authentication"
- "Create a log rotation script for system administration"
"""
    console.print(Panel(examples_text, title="clicod Examples (JSON Format)", border_style="blue"))

@cli.command()
def about():
    """About clicod"""
    config = click.get_current_context().obj['config']
    
    about_text = f"""
## 🚀 clicod - CLI Code Generator (JSON Format)

**Version:** 1.0.0 (Enhanced JSON)
**Configuration:** {config.config_file}

**New Features:**
- Structured JSON responses from AI
- Enhanced dependency tracking
- Comprehensive code documentation
- Better error handling and parsing
- Rich terminal output with syntax highlighting

**Configuration stored in:** `{config.config_file}`
"""
    console.print(Panel(about_text, title="About clicod (JSON Enhanced)", border_style="cyan"))

if __name__ == '__main__':
    cli()
