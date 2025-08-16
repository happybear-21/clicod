import os
import sys
import json
import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.syntax import Syntax
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
import time
import re
import getpass

console = Console()


class ClicodConfig:
    """Configuration management for clicod"""

    def __init__(self):
        self.config_dir = Path.home() / ".clicod"
        self.config_file = self.config_dir / "config.json"
        self.config_dir.mkdir(exist_ok=True)
        self.config = self._load_config()

    def _load_config(self):
        """Load configuration from file"""
        default_config = {
            "gemini_api_key": None,
            "default_model": "gemini-2.5-flash",
            "save_location": str(Path.cwd()),
            "auto_save": False,
            "streaming": False,
            "json_format": True,
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    saved_config = json.load(f)
                    default_config.update(saved_config)
            except (json.JSONDecodeError, FileNotFoundError):
                console.print(
                    "⚠️ [yellow]Config file corrupted, using defaults[/yellow]"
                )

        return default_config

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, "w") as f:
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
        api_key = self.get("gemini_api_key")
        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            console.print(
                "🔐 [yellow]Gemini API key not found in configuration[/yellow]"
            )
            if Confirm.ask("Would you like to set it now?"):
                api_key = getpass.getpass("Enter your Gemini API key: ")
                if api_key:
                    self.set("gemini_api_key", api_key)
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
            self.model_name = model_name or self.config.get(
                "default_model", "gemini-2.5-flash"
            )
            console.print(f"✅ [green]clicod using model: {self.model_name}[/green]")
        except ImportError:
            console.print("❌ [red]Error: google-genai SDK not found![/red]")
            console.print("Install with: pip install google-genai")
            sys.exit(1)
        except Exception as e:
            console.print(f"❌ [red]Error configuring Gemini API: {str(e)}[/red]")
            sys.exit(1)

        # Highly detailed system prompt with comprehensive instructions
        self.system_prompt = """
You are an elite Perl systems programmer with 20+ years of experience in enterprise-level software development, 
security-focused applications, system administration, data processing, and web development. You write production-ready, 
secure, efficient, and maintainable Perl code following all modern best practices.

=== CORE PROGRAMMING PRINCIPLES ===
1. SECURITY FIRST: Always implement input validation, sanitization, and secure coding practices
2. ERROR HANDLING: Comprehensive error checking with meaningful messages and graceful degradation
3. PERFORMANCE: Write efficient code with proper resource management and optimization
4. MAINTAINABILITY: Clear documentation, modular design, and readable code structure
5. PORTABILITY: Code that works across different Unix/Linux systems and Perl versions
6. TESTING: Include test cases and validation mechanisms
7. LOGGING: Implement proper logging and debugging capabilities

=== SECURITY REQUIREMENTS ===
- Input Validation: Validate and sanitize ALL user inputs using proper regex patterns
- Taint Mode: Use -T flag and untaint data safely when needed
- File Operations: Use secure file handling with proper permissions and path validation
- SQL Injection Prevention: Use prepared statements and parameter binding
- XSS Prevention: Escape all output in web applications
- Command Injection: Never use system() with user input, use proper escaping
- Path Traversal: Validate file paths and prevent directory traversal attacks
- Privilege Management: Run with minimal required privileges
- Cryptography: Use proven libraries for encryption/hashing (Crypt::* modules)
- Session Management: Secure session handling in web applications

=== CODE STRUCTURE REQUIREMENTS ===
- Always use: strict, warnings, autodie (when appropriate)
- Use modern Perl idioms: given/when, say, state variables
- Implement proper OOP when needed using Moo/Moose or core OOP
- Use appropriate data structures: references, complex data structures
- Implement proper signal handling for long-running processes
- Use proper scoping and lexical variables
- Implement configuration management
- Use proper command-line argument parsing (Getopt::Long)

=== RESPONSE FORMAT ===
Structure your response using these EXACT section markers:

=== DESCRIPTION_START ===
Provide a comprehensive description of what the script/system does, its purpose, 
use cases, and how it fits into typical workflows. Include architectural overview 
for complex systems.
=== DESCRIPTION_END ===

=== MAIN_SCRIPT_START ===
#!/usr/bin/env perl
use strict;
use warnings;
use autodie;

# Your main Perl script here - this should be complete and production-ready
# Include all necessary modules, error handling, logging, and security measures
=== MAIN_SCRIPT_END ===

=== ADDITIONAL_FILE_START ===
FILENAME: config.pl
DESCRIPTION: Configuration file or module
TYPE: config|module|test|documentation|helper
#!/usr/bin/env perl
# Additional file content here
=== ADDITIONAL_FILE_END ===

=== ADDITIONAL_FILE_START ===
FILENAME: MyModule.pm
DESCRIPTION: Custom module for specific functionality
TYPE: module
package MyModule;
use strict;
use warnings;
# Module content here
=== ADDITIONAL_FILE_END ===

=== SECURITY_MEASURES_START ===
List all security measures implemented in the code:
- Input validation patterns used
- Security modules employed
- Potential security risks addressed
- Recommended security configurations
- File permission requirements
=== SECURITY_MEASURES_END ===

=== DEPENDENCIES_START ===
Core Modules: List::Util, File::Spec, Getopt::Long, Pod::Usage
CPAN Modules: DBI (cpan install DBI - Database connectivity), Moo (cpan install Moo - Modern OOP)
System Requirements: perl 5.14+, specific OS requirements
Security Modules: Crypt::CBC, Digest::SHA, Data::Validate::IP
Development Tools: Perl::Critic, Perl::Tidy, Test::More
=== DEPENDENCIES_END ===

=== INSTALLATION_START ===
Step-by-step installation and setup instructions including:
1. System requirements verification
2. CPAN module installation
3. Configuration steps
4. Permission settings
5. Initial testing
=== INSTALLATION_END ===

=== CONFIGURATION_START ===
Configuration options, environment variables, and customization:
- Configuration file format and location
- Environment variables used
- Runtime configuration options
- Security configuration recommendations
=== CONFIGURATION_END ===

=== USAGE_EXAMPLES_START ===
perl script.pl --help
perl script.pl --config /etc/myapp.conf --verbose
perl script.pl --input data.csv --output results.json --secure-mode
sudo perl script.pl --system-wide --log-level debug
=== USAGE_EXAMPLES_END ===

=== FEATURES_START ===
- Comprehensive error handling with detailed logging
- Multi-threaded/forked processing capabilities (when applicable)
- Configuration file support with validation
- Secure file operations with permission checking
- Performance monitoring and optimization
- Signal handling for graceful shutdown
- Memory management and resource cleanup
- Cross-platform compatibility
=== FEATURES_END ===

=== FUNCTIONS_START ===
validate_input: Validates and sanitizes user input - Parameters: input_string, validation_type
process_data: Main data processing function - Parameters: data_ref, options_ref
secure_file_write: Writes files securely with proper permissions - Parameters: filename, content, mode
error_handler: Centralized error handling and logging - Parameters: error_message, severity_level
cleanup_resources: Cleans up resources and temporary files - Parameters: resource_list
=== FUNCTIONS_END ===

=== TESTING_START ===
Test Case 1: Input validation with malicious data
Test Case 2: File operations with invalid permissions
Test Case 3: Performance testing with large datasets
Test Case 4: Security testing for injection attacks
Test Case 5: Error handling with network failures
Sample Input: Various test data including edge cases
Expected Output: Proper handling of all scenarios with appropriate logging
Unit Tests: Individual function testing
Integration Tests: End-to-end system testing
Security Tests: Penetration testing scenarios
=== TESTING_END ===

=== ERROR_HANDLING_START ===
Comprehensive error handling strategy:
- Input validation errors
- File system errors
- Network connectivity issues
- Database connection problems
- Memory/resource exhaustion
- Signal handling (SIGINT, SIGTERM, etc.)
- Graceful degradation strategies
=== ERROR_HANDLING_END ===

=== PERFORMANCE_START ===
Performance considerations and optimizations:
- Memory usage patterns
- CPU optimization techniques
- I/O optimization strategies
- Caching mechanisms
- Parallel processing options
- Benchmarking recommendations
=== PERFORMANCE_END ===

=== MONITORING_START ===
Logging and monitoring capabilities:
- Log levels and categories
- Performance metrics collection
- Health check endpoints (for daemons)
- Debug information availability
- Audit trail creation
=== MONITORING_END ===

=== DEPLOYMENT_START ===
Production deployment guidelines:
- Server requirements
- Directory structure
- File permissions
- Service configuration
- Monitoring setup
- Backup procedures
- Update procedures
=== DEPLOYMENT_END ===

=== BEST_PRACTICES_START ===
- Modern Perl practices (use strict/warnings/autodie)
- Comprehensive input validation and sanitization
- Secure file handling with proper permissions
- Proper error handling with meaningful messages
- Resource management and cleanup
- Modular code design with reusable components
- Comprehensive logging and debugging support
- Performance optimization and memory management
- Cross-platform compatibility considerations
- Code documentation and inline comments
- Test-driven development practices
- Security-first development approach
=== BEST_PRACTICES_END ===

=== NOTES_START ===
Important implementation notes, security considerations, performance tips, 
deployment recommendations, and maintenance guidelines. Include any special 
requirements or limitations.
=== NOTES_END ===

=== MANDATORY REQUIREMENTS ===
1. ALL code must include comprehensive input validation
2. ALL file operations must include proper error handling
3. ALL scripts must support command-line arguments with help text
4. ALL scripts must include proper logging capabilities
5. ALL scripts must handle signals gracefully
6. ALL database operations must use prepared statements
7. ALL web-facing code must prevent XSS and injection attacks
8. ALL scripts must include proper resource cleanup
9. Generate multiple files when the complexity requires it (modules, configs, tests)
10. Include proper POD documentation in all modules

=== CODE GENERATION RULES ===
- Always start main scripts with proper shebang and pragmas
- Use Getopt::Long for command-line argument parsing
- Implement proper POD documentation
- Use proper Perl OOP (Moo/Moose) for complex applications
- Include comprehensive error messages with error codes
- Implement proper logging using Log::Log4perl or similar
- Use appropriate CPAN modules instead of reinventing the wheel
- Follow PerlBP (Perl Best Practices) guidelines
- Include proper resource management (files, database connections, etc.)
- Implement proper signal handling for daemons and long-running processes

Generate production-ready, enterprise-level Perl code that can be deployed in 
real-world environments with confidence. Focus on security, performance, 
maintainability, and robustness.
"""

    def _extract_section(self, text: str, start_marker: str, end_marker: str) -> str:
        """Extract content between section markers with improved handling"""
        try:
            start_pattern = re.escape(start_marker)
            end_pattern = re.escape(end_marker)
            pattern = f"{start_pattern}(.*?){end_pattern}"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                # Remove extra whitespace and clean up
                lines = content.split("\n")
                cleaned_lines = []
                for line in lines:
                    cleaned_lines.append(line.rstrip())
                return "\n".join(cleaned_lines)
            return ""
        except Exception:
            return ""

    def _extract_main_script(self, text: str) -> str:
        """Extract main Perl script with enhanced detection"""
        # Primary method: Section markers
        main_script = self._extract_section(
            text, "=== MAIN_SCRIPT_START ===", "=== MAIN_SCRIPT_END ==="
        )
        if main_script and len(main_script) > 50:
            return main_script

        # Fallback methods for robustness
        patterns = [
            r"``````",
            r"``````",
            r"``````",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                if len(match.strip()) > 50 and (
                    "use strict" in match or "use warnings" in match
                ):
                    return match.strip()

        # Look for shebang-based scripts
        lines = text.split("\n")
        script_start = -1

        for i, line in enumerate(lines):
            if line.strip().startswith("#!/") and "perl" in line.lower():
                script_start = i
                break

        if script_start != -1:
            script_lines = []
            for i in range(script_start, len(lines)):
                line = lines[i]
                # Stop if we hit another section marker
                if line.strip().startswith("===") and "END" in line.upper():
                    break
                script_lines.append(line)

            if script_lines and len("\n".join(script_lines).strip()) > 50:
                return "\n".join(script_lines)

        return ""

    def _extract_additional_files(self, text: str) -> List[Dict[str, str]]:
        """Extract multiple additional files from the response"""
        additional_files = []

        # Find all additional file blocks
        pattern = r"=== ADDITIONAL_FILE_START ===(.*?)=== ADDITIONAL_FILE_END ==="
        matches = re.findall(pattern, text, re.DOTALL)

        for match in matches:
            file_info = {
                "filename": "additional.pl",
                "content": "",
                "description": "Additional file",
                "type": "helper",
            }

            lines = match.strip().split("\n")
            content_lines = []

            for line in lines:
                line = line.strip()
                if line.startswith("FILENAME:"):
                    file_info["filename"] = line.replace("FILENAME:", "").strip()
                elif line.startswith("DESCRIPTION:"):
                    file_info["description"] = line.replace("DESCRIPTION:", "").strip()
                elif line.startswith("TYPE:"):
                    file_info["type"] = line.replace("TYPE:", "").strip()
                elif (
                    not line.startswith("FILENAME:")
                    and not line.startswith("DESCRIPTION:")
                    and not line.startswith("TYPE:")
                ):
                    content_lines.append(line)

            # Join content lines back together, preserving original spacing
            if content_lines:
                # Find the actual content by skipping metadata lines
                content_start = 0
                full_lines = match.strip().split("\n")

                for i, line in enumerate(full_lines):
                    if not line.strip().startswith(
                        ("FILENAME:", "DESCRIPTION:", "TYPE:")
                    ):
                        content_start = i
                        break

                file_info["content"] = "\n".join(full_lines[content_start:]).strip()

            if file_info["content"] and len(file_info["content"]) > 10:
                additional_files.append(file_info)

        return additional_files

    def _extract_security_measures(self, text: str) -> List[str]:
        """Extract security measures implemented"""
        security_text = self._extract_section(
            text, "=== SECURITY_MEASURES_START ===", "=== SECURITY_MEASURES_END ==="
        )

        if not security_text:
            return [
                "Input validation implemented",
                "Error handling included",
                "Secure file operations",
            ]

        measures = []
        for line in security_text.split("\n"):
            line = line.strip()
            if line and not line.startswith("==="):
                line = re.sub(r"^[-*•]\s*", "", line)
                if line:
                    measures.append(line)

        return measures if measures else ["Basic security measures implemented"]

    def _extract_installation_steps(self, text: str) -> List[str]:
        """Extract installation instructions"""
        install_text = self._extract_section(
            text, "=== INSTALLATION_START ===", "=== INSTALLATION_END ==="
        )

        if not install_text:
            return [
                "Install required CPAN modules",
                "Set appropriate permissions",
                "Configure as needed",
            ]

        steps = []
        for line in install_text.split("\n"):
            line = line.strip()
            if line and not line.startswith("==="):
                # Clean up numbered lists
                line = re.sub(r"^\d+\.\s*", "", line)
                line = re.sub(r"^[-*•]\s*", "", line)
                if line:
                    steps.append(line)

        return steps if steps else ["Follow standard Perl installation procedures"]

    def _extract_configuration(self, text: str) -> Dict[str, Any]:
        """Extract configuration information"""
        config_text = self._extract_section(
            text, "=== CONFIGURATION_START ===", "=== CONFIGURATION_END ==="
        )

        config_info = {"config_file": "", "environment_vars": [], "options": []}

        if not config_text:
            return config_info

        for line in config_text.split("\n"):
            line = line.strip()
            if "config file" in line.lower():
                config_info["config_file"] = line
            elif "environment" in line.lower() or line.startswith("$"):
                config_info["environment_vars"].append(line)
            elif line and not line.startswith("==="):
                config_info["options"].append(line)

        return config_info

    def _extract_dependencies(self, text: str) -> Dict[str, List]:
        """Extract comprehensive dependency information"""
        deps_text = self._extract_section(
            text, "=== DEPENDENCIES_START ===", "=== DEPENDENCIES_END ==="
        )

        dependencies = {
            "core_modules": [],
            "cpan_modules": [],
            "system_requirements": [],
            "security_modules": [],
            "development_tools": [],
        }

        if not deps_text:
            # Fallback: scan for use/require statements
            use_pattern = r"(?:use|require)\s+([\w:]+)"
            for match in re.finditer(use_pattern, text):
                module = match.group(1)
                if module not in ["strict", "warnings", "autodie"] and "::" in module:
                    dependencies["core_modules"].append(module)
            return dependencies

        lines = deps_text.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("Core Modules:"):
                modules = line.replace("Core Modules:", "").strip()
                if modules:
                    dependencies["core_modules"] = [
                        m.strip() for m in modules.split(",")
                    ]

            elif line.startswith("CPAN Modules:"):
                modules_text = line.replace("CPAN Modules:", "").strip()
                if modules_text:
                    for module_info in modules_text.split(","):
                        module_info = module_info.strip()
                        if "(" in module_info:
                            name = module_info.split("(")[0].strip()
                            details = module_info.split("(")[1].replace(")", "")
                            dependencies["cpan_modules"].append(
                                {
                                    "name": name,
                                    "install_command": f"cpan install {name}",
                                    "purpose": (
                                        details.split(" - ")[-1]
                                        if " - " in details
                                        else "Required module"
                                    ),
                                }
                            )
                        else:
                            dependencies["cpan_modules"].append(
                                {
                                    "name": module_info,
                                    "install_command": f"cpan install {module_info}",
                                    "purpose": "Required module",
                                }
                            )

            elif line.startswith("System Requirements:"):
                reqs = line.replace("System Requirements:", "").strip()
                if reqs:
                    dependencies["system_requirements"] = [
                        r.strip() for r in reqs.split(",")
                    ]

            elif line.startswith("Security Modules:"):
                modules = line.replace("Security Modules:", "").strip()
                if modules:
                    dependencies["security_modules"] = [
                        m.strip() for m in modules.split(",")
                    ]

            elif line.startswith("Development Tools:"):
                tools = line.replace("Development Tools:", "").strip()
                if tools:
                    dependencies["development_tools"] = [
                        t.strip() for t in tools.split(",")
                    ]

        return dependencies

    def _extract_monitoring_info(self, text: str) -> Dict[str, Any]:
        """Extract monitoring and logging information"""
        monitoring_text = self._extract_section(
            text, "=== MONITORING_START ===", "=== MONITORING_END ==="
        )

        monitoring_info = {
            "log_levels": [],
            "metrics": [],
            "health_checks": [],
            "debug_info": [],
        }

        if not monitoring_text:
            return monitoring_info

        for line in monitoring_text.split("\n"):
            line = line.strip()
            if "log level" in line.lower():
                monitoring_info["log_levels"].append(line)
            elif "metric" in line.lower() or "performance" in line.lower():
                monitoring_info["metrics"].append(line)
            elif "health" in line.lower() or "check" in line.lower():
                monitoring_info["health_checks"].append(line)
            elif "debug" in line.lower():
                monitoring_info["debug_info"].append(line)

        return monitoring_info

    def _extract_deployment_info(self, text: str) -> List[str]:
        """Extract deployment guidelines"""
        deployment_text = self._extract_section(
            text, "=== DEPLOYMENT_START ===", "=== DEPLOYMENT_END ==="
        )

        if not deployment_text:
            return [
                "Deploy to appropriate server environment",
                "Set proper file permissions",
                "Configure monitoring",
            ]

        deployment_steps = []
        for line in deployment_text.split("\n"):
            line = line.strip()
            if line and not line.startswith("==="):
                line = re.sub(r"^[-*•]\s*", "", line)
                if line:
                    deployment_steps.append(line)

        return (
            deployment_steps
            if deployment_steps
            else ["Follow standard deployment procedures"]
        )

    def _parse_structured_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the comprehensive structured response"""
        try:
            parsed_data = {
                "status": "success",
                "response_type": "perl_code_generation",
                "metadata": {
                    "model_used": self.model_name,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "complexity_level": "intermediate",
                    "estimated_lines": 0,
                    "file_count": 1,
                },
                "perl_code": {"main_script": "", "additional_files": []},
                "dependencies": {
                    "core_modules": [],
                    "cpan_modules": [],
                    "system_requirements": [],
                    "security_modules": [],
                    "development_tools": [],
                },
                "documentation": {
                    "description": "",
                    "usage_examples": [],
                    "features": [],
                    "notes": [],
                    "installation_steps": [],
                    "configuration": {},
                },
                "code_structure": {
                    "functions": [],
                    "main_sections": ["Main Logic", "Helper Functions"],
                },
                "security": {"measures": [], "considerations": []},
                "performance": {"optimizations": [], "monitoring": {}},
                "deployment": {"steps": [], "requirements": []},
                "best_practices": [],
                "testing": {
                    "test_cases": [],
                    "sample_input": "",
                    "expected_output": "",
                },
                "error_handling": [],
            }

            # Extract main script (most critical)
            main_script = self._extract_main_script(response_text)
            if not main_script:
                parsed_data["status"] = "error"
                return parsed_data

            parsed_data["perl_code"]["main_script"] = main_script
            parsed_data["metadata"]["estimated_lines"] = len(main_script.split("\n"))

            # Extract additional files
            additional_files = self._extract_additional_files(response_text)
            parsed_data["perl_code"]["additional_files"] = additional_files
            parsed_data["metadata"]["file_count"] = 1 + len(additional_files)

            # Extract description
            description = self._extract_section(
                response_text, "=== DESCRIPTION_START ===", "=== DESCRIPTION_END ==="
            )
            if not description:
                description = "Comprehensive Perl script generated by clicod with enterprise-level features"
            parsed_data["documentation"]["description"] = description

            # Extract comprehensive information
            parsed_data["dependencies"] = self._extract_dependencies(response_text)
            parsed_data["documentation"]["usage_examples"] = (
                self._extract_usage_examples(response_text)
            )
            parsed_data["documentation"]["features"] = self._extract_features(
                response_text
            )
            parsed_data["documentation"]["installation_steps"] = (
                self._extract_installation_steps(response_text)
            )
            parsed_data["documentation"]["configuration"] = self._extract_configuration(
                response_text
            )
            parsed_data["code_structure"]["functions"] = self._extract_functions(
                response_text
            )
            parsed_data["security"]["measures"] = self._extract_security_measures(
                response_text
            )
            parsed_data["performance"]["monitoring"] = self._extract_monitoring_info(
                response_text
            )
            parsed_data["deployment"]["steps"] = self._extract_deployment_info(
                response_text
            )
            parsed_data["testing"] = self._extract_testing_info(response_text)
            parsed_data["best_practices"] = self._extract_best_practices(response_text)

            # Extract error handling
            error_handling = self._extract_section(
                response_text,
                "=== ERROR_HANDLING_START ===",
                "=== ERROR_HANDLING_END ===",
            )
            if error_handling:
                parsed_data["error_handling"] = [
                    line.strip() for line in error_handling.split("\n") if line.strip()
                ]

            # Extract notes
            notes = self._extract_section(
                response_text, "=== NOTES_START ===", "=== NOTES_END ==="
            )
            if notes:
                parsed_data["documentation"]["notes"] = [notes]

            # Determine complexity based on comprehensive analysis
            total_lines = parsed_data["metadata"]["estimated_lines"]
            function_count = len(parsed_data["code_structure"]["functions"])
            file_count = parsed_data["metadata"]["file_count"]

            if total_lines > 200 or function_count > 8 or file_count > 3:
                parsed_data["metadata"]["complexity_level"] = "advanced"
            elif total_lines < 50 and function_count <= 2 and file_count == 1:
                parsed_data["metadata"]["complexity_level"] = "beginner"

            return parsed_data

        except Exception as e:
            console.print(
                f"🔍 [yellow]Error parsing structured response: {str(e)}[/yellow]"
            )
            return {
                "status": "error",
                "response_type": "perl_code_generation",
                "metadata": {
                    "model_used": self.model_name,
                    "complexity_level": "unknown",
                    "estimated_lines": 0,
                },
                "perl_code": {"main_script": "", "additional_files": []},
                "dependencies": {
                    "core_modules": [],
                    "cpan_modules": [],
                    "system_requirements": [],
                },
                "documentation": {
                    "description": "Error parsing response",
                    "usage_examples": [],
                    "features": [],
                    "notes": [],
                },
                "code_structure": {"functions": [], "main_sections": []},
                "security": {"measures": []},
                "best_practices": [],
                "testing": {
                    "test_cases": [],
                    "sample_input": "",
                    "expected_output": "",
                },
            }

    def _extract_usage_examples(self, text: str) -> List[str]:
        """Extract comprehensive usage examples"""
        usage_text = self._extract_section(
            text, "=== USAGE_EXAMPLES_START ===", "=== USAGE_EXAMPLES_END ==="
        )

        if not usage_text:
            return ["perl script.pl --help", "perl script.pl --config config.conf"]

        examples = []
        for line in usage_text.split("\n"):
            line = line.strip()
            if (
                line
                and not line.startswith("===")
                and ("perl" in line or line.startswith("./"))
            ):
                examples.append(line)

        return examples if examples else ["perl script.pl --help"]

    def _extract_features(self, text: str) -> List[str]:
        """Extract comprehensive features list"""
        features_text = self._extract_section(
            text, "=== FEATURES_START ===", "=== FEATURES_END ==="
        )

        if not features_text:
            return [
                "Modern Perl implementation",
                "Comprehensive error handling",
                "Security-focused design",
            ]

        features = []
        for line in features_text.split("\n"):
            line = line.strip()
            if line and not line.startswith("==="):
                line = re.sub(r"^[-*•]\s*", "", line)
                if line:
                    features.append(line)

        return features if features else ["Enterprise-level Perl implementation"]

    def _extract_functions(self, text: str) -> List[Dict[str, Any]]:
        """Extract comprehensive function information"""
        functions_text = self._extract_section(
            text, "=== FUNCTIONS_START ===", "=== FUNCTIONS_END ==="
        )

        if not functions_text:
            # Fallback: scan main script for function definitions
            main_script = self._extract_main_script(text)
            functions = []
            for line in main_script.split("\n"):
                if line.strip().startswith("sub "):
                    func_match = re.match(r"sub\s+(\w+)", line.strip())
                    if func_match:
                        functions.append(
                            {
                                "name": func_match.group(1),
                                "description": "Function defined in main script",
                                "parameters": [],
                            }
                        )
            return functions

        functions = []
        for line in functions_text.split("\n"):
            line = line.strip()
            if ":" in line and "Parameters:" in line:
                parts = line.split(":", 1)
                name = parts[0].strip()
                desc_and_params = parts[1]

                if "Parameters:" in desc_and_params:
                    desc_part, params_part = desc_and_params.split("Parameters:", 1)
                    description = desc_part.strip(" -")
                    params = [p.strip() for p in params_part.split(",") if p.strip()]
                else:
                    description = desc_and_params.strip(" -")
                    params = []

                functions.append(
                    {"name": name, "description": description, "parameters": params}
                )

        return functions

    def _extract_testing_info(self, text: str) -> Dict[str, Any]:
        """Extract comprehensive testing information"""
        testing_text = self._extract_section(
            text, "=== TESTING_START ===", "=== TESTING_END ==="
        )

        testing_info = {
            "test_cases": [],
            "sample_input": "",
            "expected_output": "",
            "unit_tests": [],
            "integration_tests": [],
            "security_tests": [],
        }

        if not testing_text:
            return testing_info

        lines = testing_text.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("Test Case"):
                testing_info["test_cases"].append(line)
            elif line.startswith("Sample Input:"):
                testing_info["sample_input"] = line.replace("Sample Input:", "").strip()
            elif line.startswith("Expected Output:"):
                testing_info["expected_output"] = line.replace(
                    "Expected Output:", ""
                ).strip()
            elif line.startswith("Unit Tests:"):
                testing_info["unit_tests"].append(
                    line.replace("Unit Tests:", "").strip()
                )
            elif line.startswith("Integration Tests:"):
                testing_info["integration_tests"].append(
                    line.replace("Integration Tests:", "").strip()
                )
            elif line.startswith("Security Tests:"):
                testing_info["security_tests"].append(
                    line.replace("Security Tests:", "").strip()
                )

        return testing_info

    def _extract_best_practices(self, text: str) -> List[str]:
        """Extract comprehensive best practices"""
        practices_text = self._extract_section(
            text, "=== BEST_PRACTICES_START ===", "=== BEST_PRACTICES_END ==="
        )

        if not practices_text:
            return [
                "Modern Perl practices (strict/warnings/autodie)",
                "Comprehensive input validation",
                "Secure file operations",
                "Proper error handling",
                "Performance optimization",
            ]

        practices = []
        for line in practices_text.split("\n"):
            line = line.strip()
            if line and not line.startswith("==="):
                line = re.sub(r"^[-*•]\s*", "", line)
                if line:
                    practices.append(line)

        return (
            practices if practices else ["Enterprise-level best practices implemented"]
        )

    def _generate_with_retry(
        self, prompt: str, max_retries: int = 3
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """Generate comprehensive code with retry logic"""

        enhanced_prompt = f"""
{self.system_prompt}

User Request: {prompt}

Please generate a comprehensive Perl solution following all the detailed requirements above.
Focus on creating production-ready, secure, and maintainable code with multiple files if needed.
Include all security measures, performance optimizations, and enterprise-level features.
"""

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    console.print(
                        f"🔄 [yellow]Retry {attempt + 1}/{max_retries} - requesting comprehensive solution...[/yellow]"
                    )
                    enhanced_prompt += f"\n\nATTEMPT {attempt + 1}: Please ensure you include all section markers and provide complete, production-ready Perl code with comprehensive security measures."

                start_time = time.time()
                console.print(
                    f"🤖 [yellow]Generating comprehensive solution (attempt {attempt + 1})...[/yellow]"
                )

                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=enhanced_prompt,
                    config={
                        "temperature": 0.1,  # Lower for more consistent, professional output
                        "top_p": 0.9,
                        "top_k": 40,
                        "max_output_tokens": 8000,  # Increased for comprehensive responses
                    },
                )

                elapsed_time = time.time() - start_time
                if elapsed_time > 15:
                    console.print(
                        f"⏱️ [blue]Model took {elapsed_time:.1f}s (generating comprehensive solution)[/blue]"
                    )

                if not response.text:
                    console.print(
                        f"❌ [red]Attempt {attempt + 1}: No response from model[/red]"
                    )
                    continue

                # Parse using enhanced section-based method
                parsed_response = self._parse_structured_response(response.text)

                # Validate comprehensive solution
                main_script = parsed_response.get("perl_code", {}).get(
                    "main_script", ""
                )
                additional_files = parsed_response.get("perl_code", {}).get(
                    "additional_files", []
                )

                if main_script and len(main_script.strip()) > 50:
                    console.print(
                        f"✅ [green]Comprehensive solution generated on attempt {attempt + 1}[/green]"
                    )
                    if additional_files:
                        console.print(
                            f"📁 [blue]Generated {len(additional_files)} additional files[/blue]"
                        )
                    return parsed_response, response.text
                else:
                    console.print(
                        f"❌ [red]Attempt {attempt + 1}: Solution incomplete[/red]"
                    )
                    if attempt < max_retries - 1:
                        console.print(
                            f"🔍 [yellow]Response preview: {response.text[:200]}...[/yellow]"
                        )
                        time.sleep(2)

            except Exception as e:
                console.print(f"❌ [red]Attempt {attempt + 1} error: {str(e)}[/red]")
                if attempt < max_retries - 1:
                    time.sleep(2)

        return None, None

    def generate_code(
        self,
        prompt: str,
        save_to_file: Optional[bool] = None,
        filename: Optional[str] = None,
    ) -> Tuple[Optional[Dict], Optional[str], Optional[Dict]]:
        """Generate comprehensive enterprise-level code"""
        try:
            if save_to_file is None:
                save_to_file = self.config.get("auto_save", False)

            console.print("🚀 [blue]Starting comprehensive code generation...[/blue]")
            console.print(
                "🔒 [green]Enterprise-level security and best practices enabled[/green]"
            )

            parsed_response, raw_response = self._generate_with_retry(
                prompt, max_retries=3
            )

            if parsed_response and parsed_response.get("status") == "success":
                self._render_comprehensive_output(parsed_response)

                main_script = parsed_response.get("perl_code", {}).get(
                    "main_script", ""
                )
                dependencies = parsed_response.get("dependencies", {})

                if main_script and save_to_file:
                    self._save_comprehensive_code(parsed_response, filename)

                return parsed_response, main_script, dependencies
            else:
                console.print(
                    "❌ [red]Failed to generate comprehensive solution after 3 attempts[/red]"
                )
                if raw_response:
                    console.print("📄 [yellow]Last raw response:[/yellow]")
                    console.print(
                        Panel(
                            raw_response[:500] + "...",
                            title="Raw Response (Truncated)",
                            border_style="yellow",
                        )
                    )
                return None, None, None

        except Exception as e:
            console.print(
                f"❌ [red]Error generating comprehensive code: {str(e)}[/red]"
            )
            return None, None, None

    def stream_generate(self, prompt: str) -> Optional[Dict]:
        """Stream comprehensive code generation"""
        try:
            enhanced_prompt = f"""
            {self.system_prompt}

            User Request: {prompt}

            Please stream a comprehensive enterprise-level Perl solution with all security measures and best practices.
            """

            console.print(
                f"🤖 [yellow]clicod streaming comprehensive solution from {self.model_name}...[/yellow]"
            )
            start_time = time.time()

            response = self.client.models.generate_content_stream(
                model=self.model_name, contents=enhanced_prompt
            )

            full_text = ""
            console.print("📡 [blue]Streaming comprehensive response...[/blue]\n")

            chunk_count = 0
            for chunk in response:
                if chunk.text:
                    console.print(chunk.text, end="")
                    full_text += chunk.text
                    chunk_count += 1

                    if chunk_count % 50 == 0:
                        elapsed = time.time() - start_time
                        if elapsed > 20:
                            console.print(
                                f"\n⏱️ [blue]Model is generating comprehensive solution ({elapsed:.1f}s)...[/blue]"
                            )

            elapsed_time = time.time() - start_time
            if elapsed_time > 15:
                console.print(
                    f"\n⏱️ [blue]Comprehensive solution streamed in {elapsed_time:.1f}s[/blue]"
                )

            console.print(
                "\n\n🔄 [yellow]Processing comprehensive structured response...[/yellow]"
            )

            parsed_response = self._parse_structured_response(full_text)
            if parsed_response and parsed_response.get("status") == "success":
                console.print("\n" + "=" * 80)
                console.print(
                    "📊 [bold green]Successfully parsed comprehensive solution![/bold green]"
                )
                self._render_comprehensive_output(parsed_response)
                return parsed_response
            else:
                console.print(
                    "❌ [red]Failed to parse comprehensive streamed response[/red]"
                )
                console.print(
                    "🔄 [yellow]Attempting to fix with retry logic...[/yellow]"
                )
                return self._generate_with_retry(prompt, max_retries=2)[0]

        except Exception as e:
            console.print(f"❌ [red]Error streaming comprehensive code: {str(e)}[/red]")
            return None

    def _render_comprehensive_output(self, parsed_response):
        """Render comprehensive structured output with all sections"""
        console.print("\n" + "=" * 80)

        # Status and metadata
        status = parsed_response.get("status", "unknown")
        metadata = parsed_response.get("metadata", {})

        status_color = "green" if status == "success" else "red"
        console.print(
            f"📊 [bold {status_color}]Status: {status.upper()}[/bold {status_color}]"
        )

        if metadata:
            console.print(
                f"🔧 [blue]Complexity: {metadata.get('complexity_level', 'N/A')} | "
                f"Lines: {metadata.get('estimated_lines', 'N/A')} | "
                f"Files: {metadata.get('file_count', 'N/A')}[/blue]"
            )

        # Description
        documentation = parsed_response.get("documentation", {})
        if documentation.get("description"):
            # Clean markdown formatting from description for display
            description = documentation["description"]
            # Remove common markdown formatting for cleaner display
            description = re.sub(
                r"[*_]{1,2}([^*_]+)[*_]{1,2}", r"\1", description
            )  # Remove bold/italic
            description = re.sub(
                r"#{1,6}\s*([^\n]+)", r"\1", description
            )  # Remove headers
            description = re.sub(
                r"\[([^\]]+)\]\([^)]+\)", r"\1", description
            )  # Remove links
            description = re.sub(
                r"`([^`]+)`", r"\1", description
            )  # Remove code formatting

            console.print(
                Panel(
                    description,
                    title="📝 Comprehensive Description",
                    border_style="cyan",
                )
            )

        # Main Perl script
        perl_code_section = parsed_response.get("perl_code", {})
        main_script = perl_code_section.get("main_script", "")

        if main_script:
            console.print(
                Panel(
                    Syntax(main_script, "perl", theme="monokai", line_numbers=True),
                    title="🐪 Main Perl Script (Production-Ready)",
                    border_style="green",
                )
            )

        # Additional files
        additional_files = perl_code_section.get("additional_files", [])
        if additional_files:
            console.print(
                f"\n📁 [bold blue]Additional Files Generated: {len(additional_files)}[/bold blue]"
            )
            for i, file_info in enumerate(additional_files, 1):
                file_type = file_info.get("type", "helper")
                console.print(
                    Panel(
                        Syntax(
                            file_info.get("content", ""),
                            (
                                "perl"
                                if file_info.get("filename", "").endswith(".pl")
                                else "text"
                            ),
                            theme="monokai",
                        ),
                        title=f"📄 File {i}: {file_info.get('filename', 'additional.pl')} ({file_type}) - {file_info.get('description', '')}",
                        border_style="blue",
                    )
                )

        # Security measures
        security = parsed_response.get("security", {})
        if security.get("measures"):
            security_text = "\n".join(
                [f"🔒 {measure}" for measure in security["measures"]]
            )
            console.print(
                Panel(
                    security_text,
                    title="🛡️ Security Measures Implemented",
                    border_style="red",
                )
            )

        # Dependencies with enhanced display
        dependencies = parsed_response.get("dependencies", {})
        if dependencies:
            self._render_comprehensive_dependencies(dependencies)

        # Installation steps
        installation_steps = documentation.get("installation_steps", [])
        if installation_steps:
            install_text = "\n".join([f"• {step}" for step in installation_steps])
            console.print(
                Panel(
                    install_text,
                    title="📦 Installation Instructions",
                    border_style="yellow",
                )
            )

        # Configuration information
        configuration = documentation.get("configuration", {})
        if configuration:
            config_text = ""
            if configuration.get("config_file"):
                config_text += f"Config File: {configuration['config_file']}\n"
            if configuration.get("environment_vars"):
                config_text += "Environment Variables:\n"
                config_text += "\n".join(
                    [f"  • {var}" for var in configuration["environment_vars"]]
                )
            if configuration.get("options"):
                config_text += "\nOptions:\n"
                config_text += "\n".join(
                    [f"  • {opt}" for opt in configuration["options"]]
                )

            if config_text:
                console.print(
                    Panel(
                        config_text.strip(),
                        title="⚙️ Configuration",
                        border_style="cyan",
                    )
                )

        # Code structure
        code_structure = parsed_response.get("code_structure", {})
        if code_structure:
            self._render_code_structure(code_structure)

        # Usage examples
        usage_examples = documentation.get("usage_examples", [])
        if usage_examples:
            examples_text = "\n".join([f"$ {example}" for example in usage_examples])
            console.print(
                Panel(examples_text, title="🚀 Usage Examples", border_style="yellow")
            )

        # Features
        features = documentation.get("features", [])
        if features:
            features_text = "\n".join([f"✨ {feature}" for feature in features])
            console.print(
                Panel(
                    features_text, title="🌟 Enterprise Features", border_style="blue"
                )
            )

        # Performance information
        performance = parsed_response.get("performance", {})
        if performance.get("monitoring"):
            monitoring = performance["monitoring"]
            perf_text = ""
            if monitoring.get("log_levels"):
                perf_text += "Log Levels: " + ", ".join(monitoring["log_levels"]) + "\n"
            if monitoring.get("metrics"):
                perf_text += "Metrics: " + ", ".join(monitoring["metrics"]) + "\n"
            if monitoring.get("health_checks"):
                perf_text += "Health Checks: " + ", ".join(monitoring["health_checks"])

            if perf_text:
                console.print(
                    Panel(
                        perf_text.strip(),
                        title="📊 Performance & Monitoring",
                        border_style="green",
                    )
                )

        # Error handling
        error_handling = parsed_response.get("error_handling", [])
        if error_handling:
            error_text = "\n".join([f"⚠️ {error}" for error in error_handling])
            console.print(
                Panel(
                    error_text, title="🚨 Error Handling Strategy", border_style="red"
                )
            )

        # Testing information
        testing = parsed_response.get("testing", {})
        if testing:
            self._render_comprehensive_testing_info(testing)

        # Deployment information
        deployment = parsed_response.get("deployment", {})
        if deployment.get("steps"):
            deploy_text = "\n".join([f"🚀 {step}" for step in deployment["steps"]])
            console.print(
                Panel(
                    deploy_text,
                    title="🌐 Deployment Guidelines",
                    border_style="magenta",
                )
            )

        # Best practices
        best_practices = parsed_response.get("best_practices", [])
        if best_practices:
            practices_text = "\n".join([f"✓ {practice}" for practice in best_practices])
            console.print(
                Panel(
                    practices_text,
                    title="🏆 Best Practices Applied",
                    border_style="green",
                )
            )

        # Notes
        notes = documentation.get("notes", [])
        if notes:
            notes_text = "\n".join(notes)
            console.print(
                Panel(notes_text, title="📋 Important Notes", border_style="yellow")
            )

    def _render_comprehensive_dependencies(self, dependencies):
        """Render comprehensive dependencies with all categories"""
        table = Table(title="📦 Comprehensive Dependencies")
        table.add_column("Category", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Install Command", style="yellow")
        table.add_column("Purpose", style="blue")

        # Core modules
        for module in dependencies.get("core_modules", []):
            table.add_row("Core", module, "Built-in", "Perl core module")

        # CPAN modules
        for module_info in dependencies.get("cpan_modules", []):
            if isinstance(module_info, dict):
                table.add_row(
                    "CPAN",
                    module_info.get("name", ""),
                    module_info.get("install_command", ""),
                    module_info.get("purpose", ""),
                )
            else:
                table.add_row(
                    "CPAN", str(module_info), f"cpan install {module_info}", ""
                )

        # Security modules
        for module in dependencies.get("security_modules", []):
            table.add_row(
                "Security", module, f"cpan install {module}", "Security enhancement"
            )

        # Development tools
        for tool in dependencies.get("development_tools", []):
            table.add_row(
                "Dev Tool", tool, f"cpan install {tool}", "Development support"
            )

        # System requirements
        for req in dependencies.get("system_requirements", []):
            table.add_row("System", req, "See documentation", "System requirement")

        if table.rows:
            console.print(table)

    def _render_comprehensive_testing_info(self, testing):
        """Render comprehensive testing information"""
        test_content = ""

        if testing.get("test_cases"):
            test_content += "Test Cases:\n"
            test_content += "\n".join([f"• {case}" for case in testing["test_cases"]])
            test_content += "\n\n"

        if testing.get("unit_tests"):
            test_content += "Unit Tests:\n"
            test_content += "\n".join([f"• {test}" for test in testing["unit_tests"]])
            test_content += "\n\n"

        if testing.get("integration_tests"):
            test_content += "Integration Tests:\n"
            test_content += "\n".join(
                [f"• {test}" for test in testing["integration_tests"]]
            )
            test_content += "\n\n"

        if testing.get("security_tests"):
            test_content += "Security Tests:\n"
            test_content += "\n".join(
                [f"• {test}" for test in testing["security_tests"]]
            )
            test_content += "\n\n"

        if testing.get("sample_input"):
            test_content += f"Sample Input:\n{testing['sample_input']}\n\n"

        if testing.get("expected_output"):
            test_content += f"Expected Output:\n{testing['expected_output']}"

        if test_content:
            console.print(
                Panel(
                    test_content.strip(),
                    title="🧪 Comprehensive Testing Strategy",
                    border_style="magenta",
                )
            )

    def _save_comprehensive_code(self, parsed_response, filename=None):
        """Save comprehensive code solution with all files"""
        save_location = Path(self.config.get("save_location", Path.cwd()))

        if not filename:
            filename = Prompt.ask(
                "Enter main script filename", default="clicod_enterprise.pl"
            )

        if not filename.endswith(".pl"):
            filename += ".pl"

        filepath = save_location / filename

        try:
            perl_code_section = parsed_response.get("perl_code", {})
            main_script = perl_code_section.get("main_script", "")
            dependencies = parsed_response.get("dependencies", {})
            documentation = parsed_response.get("documentation", {})
            security = parsed_response.get("security", {})

            # Save main script with comprehensive header
            with open(filepath, "w") as f:
                f.write("#!/usr/bin/env perl\n")
                f.write("# Generated by clicod - Enterprise CLI Code Generator\n")
                f.write(f"# Model: {self.model_name}\n")
                f.write("# https://github.com/happybear-21/clicod\n")
                f.write("# " + "=" * 60 + "\n")
                f.write("# ENTERPRISE-LEVEL PERL SOLUTION\n")
                f.write("# Security-focused, Production-ready Implementation\n")
                f.write("# " + "=" * 60 + "\n")

                if documentation.get("description"):
                    f.write(f"# Description: {documentation['description']}\n")

                # Security information
                if security.get("measures"):
                    f.write("#\n# Security Measures Implemented:\n")
                    for measure in security["measures"]:
                        f.write(f"# - {measure}\n")

                # Dependencies
                cpan_modules = dependencies.get("cpan_modules", [])
                if cpan_modules:
                    f.write("#\n# Required CPAN modules:\n")
                    for module in cpan_modules:
                        if isinstance(module, dict):
                            f.write(f"# {module.get('install_command', '')}\n")
                        else:
                            f.write(f"# cpan install {module}\n")

                # Usage examples
                usage_examples = documentation.get("usage_examples", [])
                if usage_examples:
                    f.write("#\n# Usage examples:\n")
                    for example in usage_examples:
                        f.write(f"# {example}\n")

                # Installation steps
                install_steps = documentation.get("installation_steps", [])
                if install_steps:
                    f.write("#\n# Installation:\n")
                    for i, step in enumerate(
                        install_steps[:5], 1
                    ):  # Limit to first 5 steps
                        f.write(f"# {i}. {step}\n")

                f.write("#\n" + "# " + "=" * 60 + "\n\n")

                # Main script content
                f.write(main_script)

            # Make main script executable
            try:
                os.chmod(filepath, 0o755)
            except:
                pass

            console.print(f"✅ [green]Main script saved to {filepath}[/green]")

            # Save additional files
            additional_files = perl_code_section.get("additional_files", [])
            saved_files = [str(filepath)]

            for file_info in additional_files:
                add_filename = file_info.get("filename", "additional.pl")
                add_filepath = save_location / add_filename

                with open(add_filepath, "w") as f:
                    f.write("#!/usr/bin/env perl\n")
                    f.write("# Generated by clicod - Enterprise CLI Code Generator\n")
                    f.write(f"# File: {add_filename}\n")
                    f.write(f"# Type: {file_info.get('type', 'helper')}\n")
                    f.write(f"# Description: {file_info.get('description', '')}\n")
                    f.write("# " + "=" * 50 + "\n\n")
                    f.write(file_info.get("content", ""))

                # Make executable if it's a script
                if add_filename.endswith(".pl"):
                    try:
                        os.chmod(add_filepath, 0o755)
                    except:
                        pass

                saved_files.append(str(add_filepath))
                console.print(
                    f"✅ [green]{file_info.get('type', 'File').title()} saved: {add_filepath}[/green]"
                )

            # Show comprehensive summary
            console.print(
                f"\n🎉 [bold green]Comprehensive solution created![/bold green]"
            )
            console.print(f"📁 [blue]Total files generated: {len(saved_files)}[/blue]")

            # Show dependency installation
            all_cpan_modules = (
                dependencies.get("cpan_modules", [])
                + dependencies.get("security_modules", [])
                + dependencies.get("development_tools", [])
            )
            if all_cpan_modules:
                console.print("\n📦 [blue]Install all dependencies with:[/blue]")
                for module in all_cpan_modules:
                    if isinstance(module, dict):
                        console.print(f"   {module.get('install_command', '')}")
                    else:
                        console.print(f"   cpan install {module}")

            console.print(f"\n🚀 [blue]Run main script: perl {filepath}[/blue]")

            # Show security recommendations
            if security.get("measures"):
                console.print(f"\n🔒 [yellow]Security Notes:[/yellow]")
                for measure in security["measures"][:3]:  # Show first 3 measures
                    console.print(f"   • {measure}")

        except Exception as e:
            console.print(
                f"❌ [red]Error saving comprehensive solution: {str(e)}[/red]"
            )

    # Keep all existing methods for CLI commands and configuration
    def _render_code_structure(self, code_structure):
        """Render code structure information"""
        functions = code_structure.get("functions", [])
        if functions:
            func_table = Table(title="🔧 Functions")
            func_table.add_column("Function", style="cyan")
            func_table.add_column("Description", style="green")
            func_table.add_column("Parameters", style="yellow")

            for func in functions:
                if isinstance(func, dict):
                    params = ", ".join(func.get("parameters", []))
                    func_table.add_row(
                        func.get("name", ""), func.get("description", ""), params
                    )

            console.print(func_table)

        main_sections = code_structure.get("main_sections", [])
        if main_sections:
            sections_text = "\n".join([f"• {section}" for section in main_sections])
            console.print(
                Panel(sections_text, title="🏗️ Code Structure", border_style="blue")
            )

    def _save_structured_code(self, parsed_response, filename=None):
        """Alias for _save_comprehensive_code to maintain compatibility"""
        return self._save_comprehensive_code(parsed_response, filename)


@click.group()
@click.version_option(version="1.0.0", prog_name="clicod")
@click.option("--model", "-m", help="Specify Gemini model to use")
@click.pass_context
def cli(ctx, model):
    """
    🚀 clicod - CLI Code Generator

    Generate Perl scripts using Gemini AI with structured JSON responses.
    Configuration is stored in ~/.clicod/config.json
    """
    ctx.ensure_object(dict)
    ctx.obj["config"] = ClicodConfig()
    ctx.obj["generator"] = ClicodGenerator(model, ctx.obj["config"])


@cli.command()
@click.argument("prompt", nargs=-1, required=False)
@click.option("--save", "-s", is_flag=True, help="Save generated code to file")
@click.option("--filename", "-f", help="Specify output filename")
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode")
@click.option("--stream", is_flag=True, help="Stream response in real-time")
def generate(prompt, save, filename, interactive, stream):
    """Generate Perl code based on natural language description"""
    generator = click.get_current_context().obj["generator"]
    config = click.get_current_context().obj["config"]

    if not stream:
        stream = config.get("streaming", False)

    if interactive:
        console.print(
            "🚀 [bold blue]clicod - Interactive Structured Code Generation[/bold blue]"
        )
        console.print(f"Using model: [green]{generator.model_name}[/green]")
        console.print(
            "Commands: 'exit', 'quit', 'config', 'save on/off', 'stream on/off'\n"
        )

        try:
            while True:
                user_input = Prompt.ask(f"\n[bold cyan]📝You >[/bold cyan]")

                if user_input.lower() in ["exit", "quit", "q"]:
                    console.print("👋 [yellow]Thanks for using clicod![/yellow]")
                    break

                if user_input.lower() == "config":
                    _show_current_config(config)
                    continue

                if user_input.lower().startswith("save "):
                    setting = user_input.split(" ", 1)[1].lower()
                    if setting in ["on", "true", "yes"]:
                        config.set("auto_save", True)
                        config.save_config()
                        console.print("✅ [green]Auto-save enabled[/green]")
                    elif setting in ["off", "false", "no"]:
                        config.set("auto_save", False)
                        config.save_config()
                        console.print("✅ [green]Auto-save disabled[/green]")
                    continue

                if user_input.lower().startswith("stream "):
                    setting = user_input.split(" ", 1)[1].lower()
                    if setting in ["on", "true", "yes"]:
                        stream = True
                        console.print(
                            "✅ [green]Streaming enabled for this session[/green]"
                        )
                    elif setting in ["off", "false", "no"]:
                        stream = False
                        console.print(
                            "✅ [green]Streaming disabled for this session[/green]"
                        )
                    continue

                if stream:
                    parsed_response = generator.stream_generate(user_input)
                    if parsed_response and isinstance(parsed_response, dict):
                        perl_code = parsed_response.get("perl_code", {}).get(
                            "main_script", ""
                        )
                        if perl_code and (
                            config.get("auto_save")
                            or Confirm.ask("\n💾 Save this code to file?")
                        ):
                            save_filename = Prompt.ask(
                                "Enter filename", default="clicod_script.pl"
                            )
                            generator._save_structured_code(
                                parsed_response, save_filename
                            )
                else:
                    parsed_response, perl_code, dependencies = generator.generate_code(
                        user_input, save
                    )
                    if (
                        parsed_response
                        and not config.get("auto_save")
                        and Confirm.ask("\n💾 Save this code to file?")
                    ):
                        save_filename = Prompt.ask(
                            "Enter filename", default="clicod_script.pl"
                        )
                        generator._save_structured_code(parsed_response, save_filename)

        except KeyboardInterrupt:
            console.print("\n👋 [yellow]Thanks for using clicod![/yellow]")
    else:
        if not prompt:
            console.print(
                "❌ [red]Please provide a description or use --interactive mode[/red]"
            )
            console.print("Example: clicod generate 'Create a CSV parser script'")
            return

        prompt_text = " ".join(prompt)

        if stream:
            parsed_response = generator.stream_generate(prompt_text)
            if parsed_response and isinstance(parsed_response, dict) and save:
                generator._save_structured_code(parsed_response, filename)
        else:
            parsed_response, perl_code, dependencies = generator.generate_code(
                prompt_text, save, filename
            )


# Keep all other CLI commands the same as they were in the original code
@cli.command()
@click.option("--set-key", is_flag=True, help="Set Gemini API key")
@click.option("--set-model", help="Set default model")
@click.option("--set-save-location", help="Set default save location")
@click.option("--auto-save", type=bool, help="Enable/disable auto-save")
@click.option("--streaming", type=bool, help="Enable/disable streaming by default")
@click.option("--show", is_flag=True, help="Show current configuration")
@click.option("--reset", is_flag=True, help="Reset configuration to defaults")
def config(set_key, set_model, set_save_location, auto_save, streaming, show, reset):
    """Configure clicod settings"""
    config = click.get_current_context().obj["config"]

    if reset:
        if Confirm.ask("⚠️ Reset all configuration to defaults?"):
            config.config_file.unlink(missing_ok=True)
            console.print("✅ [green]Configuration reset to defaults[/green]")
        return

    if set_key:
        api_key = getpass.getpass("Enter your Gemini API key: ")
        if api_key:
            config.set("gemini_api_key", api_key)
            config.save_config()
            console.print("✅ [green]API key updated[/green]")

    if set_model:
        config.set("default_model", set_model)
        config.save_config()
        console.print(f"✅ [green]Default model set to: {set_model}[/green]")

    if set_save_location:
        save_path = Path(set_save_location).expanduser().resolve()
        if save_path.exists():
            config.set("save_location", str(save_path))
            config.save_config()
            console.print(f"✅ [green]Save location set to: {save_path}[/green]")
        else:
            console.print(f"❌ [red]Directory does not exist: {save_path}[/red]")

    if auto_save is not None:
        config.set("auto_save", auto_save)
        config.save_config()
        console.print(
            f"✅ [green]Auto-save {'enabled' if auto_save else 'disabled'}[/green]"
        )

    if streaming is not None:
        config.set("streaming", streaming)
        config.save_config()
        console.print(
            f"✅ [green]Streaming {'enabled' if streaming else 'disabled'}[/green]"
        )

    if show or not any(
        [
            set_key,
            set_model,
            set_save_location,
            auto_save is not None,
            streaming is not None,
        ]
    ):
        _show_current_config(config)


def _show_current_config(config):
    """Display current configuration"""
    table = Table(title="clicod Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    api_key = config.get("gemini_api_key")
    masked_key = f"{api_key[:8]}...{api_key[-4:]}" if api_key else "Not set"

    table.add_row("API Key", masked_key)
    table.add_row("Default Model", config.get("default_model", "gemini-2.5-flash"))
    table.add_row("Save Location", config.get("save_location", str(Path.cwd())))
    table.add_row("Auto Save", str(config.get("auto_save", False)))
    table.add_row("Streaming", str(config.get("streaming", False)))
    table.add_row("JSON Format", str(config.get("json_format", True)))
    table.add_row("Config File", str(config.config_file))

    console.print(table)


@cli.command()
def test():
    """Test Gemini API connection with JSON format"""
    generator = click.get_current_context().obj["generator"]
    console.print(
        f"🔌 [blue]Testing clicod connection with {generator.model_name} (JSON format)...[/blue]"
    )

    try:
        test_prompt = f"""
{generator.system_prompt}

User Request: Generate a simple Perl hello world script

This is a test request. Please respond with the exact JSON format specified.
"""

        test_response = generator.client.models.generate_content(
            model=generator.model_name, contents=test_prompt
        )

        if test_response.text:
            parsed = generator._parse_json_response(test_response.text)
            if parsed:
                console.print(
                    "✅ [green]Connection and JSON parsing successful![/green]"
                )
                console.print(
                    f"📊 [blue]Response status: {parsed.get('status', 'unknown')}[/blue]"
                )
            else:
                console.print(
                    "⚠️ [yellow]Connection successful but JSON parsing failed[/yellow]"
                )
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
    console.print(
        Panel(examples_text, title="clicod Examples (JSON Format)", border_style="blue")
    )


@cli.command()
def about():
    """About clicod"""
    config = click.get_current_context().obj["config"]

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
    console.print(
        Panel(about_text, title="About clicod (JSON Enhanced)", border_style="cyan")
    )


if __name__ == "__main__":
    cli()
