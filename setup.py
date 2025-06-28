#!/usr/bin/env python3
"""
Healthcare AI Agents Setup Script
Automated setup and configuration for CrewAI and Autogen healthcare solutions
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import argparse
from typing import List, Optional

class HealthcareAISetup:
    """Setup manager for healthcare AI agent systems"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.crewai_dir = self.root_dir / "crewai_fhir_agent"
        self.autogen_dir = self.root_dir / "autogen_fhir_agent"
        self.shared_dir = self.root_dir / "shared"
        
    def check_prerequisites(self) -> bool:
        """Check if prerequisites are installed"""
        print("🔍 Checking prerequisites...")
        
        # Check Python version
        if sys.version_info < (3, 11):
            print("❌ Python 3.11+ is required")
            return False
        print("✅ Python version: OK")
        
        # Check pip
        try:
            subprocess.run(["pip", "--version"], check=True, capture_output=True)
            print("✅ pip: OK")
        except subprocess.CalledProcessError:
            print("❌ pip is not available")
            return False
        
        # Check Docker (optional)
        try:
            subprocess.run(["docker", "--version"], check=True, capture_output=True)
            print("✅ Docker: OK")
        except subprocess.CalledProcessError:
            print("⚠️  Docker not found (optional for local development)")
        
        return True
    
    def create_virtual_environment(self, solution: str) -> bool:
        """Create virtual environment for a solution"""
        venv_path = self.root_dir / f"venv_{solution}"
        
        if venv_path.exists():
            print(f"✅ Virtual environment for {solution} already exists")
            return True
        
        try:
            print(f"🔄 Creating virtual environment for {solution}...")
            subprocess.run([
                sys.executable, "-m", "venv", str(venv_path)
            ], check=True)
            print(f"✅ Virtual environment created: {venv_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            return False
    
    def install_dependencies(self, solution: str) -> bool:
        """Install dependencies for a solution"""
        solution_dir = self.crewai_dir if solution == "crewai" else self.autogen_dir
        requirements_file = solution_dir / "requirements.txt"
        venv_path = self.root_dir / f"venv_{solution}"
        
        if not requirements_file.exists():
            print(f"❌ Requirements file not found: {requirements_file}")
            return False
        
        # Determine pip executable
        if os.name == 'nt':  # Windows
            pip_exe = venv_path / "Scripts" / "pip.exe"
        else:  # Unix/Linux/MacOS
            pip_exe = venv_path / "bin" / "pip"
        
        try:
            print(f"🔄 Installing dependencies for {solution}...")
            subprocess.run([
                str(pip_exe), "install", "-r", str(requirements_file)
            ], check=True)
            print(f"✅ Dependencies installed for {solution}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    def setup_environment_file(self) -> bool:
        """Set up environment configuration file"""
        env_example = self.root_dir / ".env.example"
        env_file = self.root_dir / ".env"
        
        if env_file.exists():
            print("✅ .env file already exists")
            return True
        
        if not env_example.exists():
            print("❌ .env.example file not found")
            return False
        
        try:
            shutil.copy(env_example, env_file)
            print("✅ Created .env file from template")
            print("⚠️  Please edit .env file with your API keys and configuration")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    
    def validate_configuration(self) -> bool:
        """Validate environment configuration"""
        env_file = self.root_dir / ".env"
        
        if not env_file.exists():
            print("❌ .env file not found")
            return False
        
        required_vars = [
            "OPENAI_API_KEY",
            "FHIR_BASE_URL",
            "FHIR_CLIENT_ID"
        ]
        
        missing_vars = []
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                
            for var in required_vars:
                if f"{var}=" not in content or f"{var}=your_" in content:
                    missing_vars.append(var)
            
            if missing_vars:
                print(f"⚠️  Please configure these variables in .env file:")
                for var in missing_vars:
                    print(f"   - {var}")
                return False
            
            print("✅ Environment configuration validated")
            return True
            
        except Exception as e:
            print(f"❌ Error reading .env file: {e}")
            return False
    
    def create_directories(self) -> bool:
        """Create necessary directories"""
        directories = [
            self.root_dir / "logs",
            self.root_dir / "data",
            self.root_dir / "tests",
            self.root_dir / "monitoring",
            self.root_dir / "nginx"
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
            print(f"✅ Created directory: {directory.name}")
        
        return True
    
    def setup_solution(self, solution: str) -> bool:
        """Set up a specific solution"""
        print(f"\n🔧 Setting up {solution.upper()} solution...")
        
        # Create virtual environment
        if not self.create_virtual_environment(solution):
            return False
        
        # Install dependencies
        if not self.install_dependencies(solution):
            return False
        
        print(f"✅ {solution.upper()} solution setup complete!")
        return True
    
    def generate_run_scripts(self):
        """Generate convenient run scripts"""
        # CrewAI run script
        crewai_script = self.root_dir / "run_crewai.py"
        with open(crewai_script, 'w') as f:
            f.write("""#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'crewai_fhir_agent'))
from main import *

if __name__ == "__main__":
    print("🏥 Starting CrewAI Healthcare Agent System...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
""")
        
        # Autogen run script
        autogen_script = self.root_dir / "run_autogen.py"
        with open(autogen_script, 'w') as f:
            f.write("""#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'autogen_fhir_agent'))
from main import *

if __name__ == "__main__":
    print("🤖 Starting Autogen Healthcare Agent System...")
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
""")
        
        # Make scripts executable
        os.chmod(crewai_script, 0o755)
        os.chmod(autogen_script, 0o755)
        
        print("✅ Generated run scripts")
    
    def setup_all(self) -> bool:
        """Set up both solutions"""
        print("🚀 Healthcare AI Agents Setup")
        print("=" * 40)
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Create directories
        if not self.create_directories():
            return False
        
        # Setup environment
        if not self.setup_environment_file():
            return False
        
        # Setup both solutions
        for solution in ["crewai", "autogen"]:
            if not self.setup_solution(solution):
                return False
        
        # Generate run scripts
        self.generate_run_scripts()
        
        print("\n🎉 Setup Complete!")
        self.print_next_steps()
        return True
    
    def print_next_steps(self):
        """Print next steps for user"""
        print("\n📋 Next Steps:")
        print("1. Edit .env file with your API keys:")
        print("   - OPENAI_API_KEY: Your OpenAI API key")
        print("   - FHIR_BASE_URL: Your FHIR server URL")
        print("   - FHIR_CLIENT_ID: Your FHIR client ID")
        
        print("\n2. Run the solutions:")
        print("   CrewAI:  python run_crewai.py")
        print("   Autogen: python run_autogen.py")
        print("   Both:    docker-compose up -d")
        
        print("\n3. Test the APIs:")
        print("   CrewAI:  http://localhost:8000")
        print("   Autogen: http://localhost:8001")
        
        print("\n4. Run demonstration:")
        print("   python demo.py")
        
        print("\n📚 Documentation:")
        print("   - README.md: Complete documentation")
        print("   - API docs: /docs endpoint on each service")
        
        print("\n⚠️  Important:")
        print("   - This is for educational/research purposes")
        print("   - Do not use for actual medical decisions")
        print("   - Ensure HIPAA compliance in production")


def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description="Healthcare AI Agents Setup")
    parser.add_argument(
        "--solution",
        choices=["crewai", "autogen", "both"],
        default="both",
        help="Which solution to set up"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check prerequisites"
    )
    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="Only validate configuration"
    )
    
    args = parser.parse_args()
    
    setup = HealthcareAISetup()
    
    if args.check_only:
        setup.check_prerequisites()
        return
    
    if args.validate_config:
        setup.validate_configuration()
        return
    
    if args.solution == "both":
        success = setup.setup_all()
    else:
        success = setup.setup_solution(args.solution)
    
    if success:
        print("\n✅ Setup completed successfully!")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main() 