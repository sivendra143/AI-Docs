"""
Check system requirements and dependencies for the AI Document Chat application.
"""
import sys
import platform
import subprocess
from pathlib import Path
from pprint import pprint

# Minimum required versions
REQUIREMENTS = {
    'python': '3.10.0',
    'pip': '21.0.0',
}

# Required Python packages with minimum versions
REQUIRED_PACKAGES = {
    'flask': '2.0.0',
    'flask_socketio': '5.0.0',
    'langchain': '0.0.200',
    'sentence_transformers': '2.2.0',
    'faiss_cpu': '1.7.0',  # or faiss_gpu if CUDA is available
    'pypdf': '3.0.0',
    'python_dotenv': '1.0.0',
    'websockets': '10.0',
    'python_docx': '0.8.11',
    'pandas': '1.3.0',
    'numpy': '1.21.0',
}

# Optional packages with their purposes
OPTIONAL_PACKAGES = {
    'faiss_gpu': 'FAISS with GPU support (if CUDA is available)',
    'torch': 'PyTorch for some embedding models',
    'transformers': 'HuggingFace Transformers for advanced models',
}

class SystemChecker:
    def __init__(self):
        self.results = {
            'system': {},
            'python': {},
            'packages': {},
            'optional': {},
            'warnings': [],
            'errors': []
        }
    
    def check_system(self):
        """Check system information."""
        system = platform.system()
        release = platform.release()
        machine = platform.machine()
        
        self.results['system'] = {
            'os': f"{system} {release} ({machine})",
            'python_version': platform.python_version(),
            'python_implementation': platform.python_implementation(),
            'python_compiler': platform.python_compiler(),
        }
        
        # Check for CUDA availability
        try:
            import torch
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                self.results['system']['cuda'] = {
                    'available': True,
                    'device': torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else 'No CUDA devices found',
                    'version': torch.version.cuda if hasattr(torch.version, 'cuda') else 'N/A'
                }
            else:
                self.results['system']['cuda'] = {'available': False}
        except ImportError:
            self.results['system']['cuda'] = {'available': False, 'error': 'PyTorch not installed'}
    
    def check_python_version(self):
        """Check if Python version meets requirements."""
        current_version = platform.python_version_tuple()
        required_version = tuple(map(int, REQUIREMENTS['python'].split('.')))
        
        self.results['python'] = {
            'current': '.'.join(current_version),
            'required': REQUIREMENTS['python'],
            'meets_requirement': current_version >= required_version
        }
        
        if not self.results['python']['meets_requirement']:
            self.results['errors'].append(
                f"Python {REQUIREMENTS['python']} or higher is required. "
                f"Current version: {'.'.join(current_version)}"
            )
    
    def check_pip_version(self):
        """Check if pip version meets requirements."""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', '--version'],
                capture_output=True,
                text=True
            )
            pip_version = result.stdout.split()[1]
            
            current_version = tuple(map(int, pip_version.split('.')))
            required_version = tuple(map(int, REQUIREMENTS['pip'].split('.')))
            
            self.results['python']['pip_version'] = pip_version
            self.results['python']['pip_meets_requirement'] = current_version >= required_version
            
            if not self.results['python']['pip_meets_requirement']:
                self.results['warnings'].append(
                    f"pip {REQUIREMENTS['pip']} or higher is recommended. "
                    f"Current version: {pip_version}"
                )
                
        except Exception as e:
            self.results['errors'].append(f"Failed to check pip version: {e}")
    
    def check_packages(self):
        """Check if required Python packages are installed and meet version requirements."""
        import importlib.metadata
        
        for package, required_version in REQUIRED_PACKAGES.items():
            try:
                # Skip faiss_gpu if not on Linux
                if package == 'faiss_gpu' and not sys.platform.startswith('linux'):
                    continue
                    
                version = importlib.metadata.version(package)
                current_version = tuple(map(int, version.split('.')[:3]))
                req_version = tuple(map(int, required_version.split('.')))
                
                self.results['packages'][package] = {
                    'installed': True,
                    'version': version,
                    'required': required_version,
                    'meets_requirement': current_version >= req_version
                }
                
                if not self.results['packages'][package]['meets_requirement']:
                    self.results['warnings'].append(
                        f"{package} {required_version} or higher is required. "
                        f"Current version: {version}"
                    )
                    
            except importlib.metadata.PackageNotFoundError:
                self.results['packages'][package] = {
                    'installed': False,
                    'required': required_version
                }
                self.results['errors'].append(f"Package not installed: {package} (required: {required_version}+)")
    
    def check_optional_packages(self):
        """Check for optional packages."""
        import importlib
        
        for package, description in OPTIONAL_PACKAGES.items():
            try:
                importlib.import_module(package.split('.')[0])
                version = importlib.metadata.version(package)
                self.results['optional'][package] = {
                    'installed': True,
                    'version': version,
                    'description': description
                }
            except (ImportError, importlib.metadata.PackageNotFoundError):
                self.results['optional'][package] = {
                    'installed': False,
                    'description': description
                }
    
    def check_directories(self):
        """Check if required directories exist and are writable."""
        required_dirs = [
            'docs',
            'vector_store',
            'uploads'
        ]
        
        self.results['directories'] = {}
        
        for dir_name in required_dirs:
            path = Path(dir_name)
            exists = path.exists()
            writable = os.access(str(path), os.W_OK) if exists else False
            
            self.results['directories'][dir_name] = {
                'exists': exists,
                'writable': writable
            }
            
            if not exists:
                self.results['warnings'].append(f"Directory not found: {dir_name}")
            elif not writable:
                self.results['errors'].append(f"Directory not writable: {dir_name}")
    
    def run_checks(self):
        """Run all checks."""
        print("🔍 Running system checks...\n")
        
        self.check_system()
        self.check_python_version()
        self.check_pip_version()
        self.check_packages()
        self.check_optional_packages()
        self.check_directories()
        
        return self.results
    
    def print_results(self):
        """Print the check results in a readable format."""
        print("\n" + "="*50)
        print("📋 System Check Results")
        print("="*50 + "\n")
        
        # Print system info
        print("🖥️  System Information:")
        print(f"  OS: {self.results['system'].get('os', 'N/A')}")
        print(f"  Python: {self.results['system'].get('python_version', 'N/A')} ({self.results['system'].get('python_implementation', 'N/A')})")
        
        if 'cuda' in self.results['system'] and self.results['system']['cuda'].get('available', False):
            cuda = self.results['system']['cuda']
            print(f"  CUDA: Available ({cuda.get('device', 'N/A')}, CUDA {cuda.get('version', 'N/A')})")
        else:
            print("  CUDA: Not available (optional for GPU acceleration)")
        
        # Print Python and pip info
        print("\n🐍 Python Environment:")
        py_info = self.results['python']
        py_status = "✅" if py_info.get('meets_requirement', False) else "❌"
        print(f"  Python Version: {py_info.get('current', 'N/A')} {py_status} (Required: {py_info.get('required', 'N/A')}+)")
        
        if 'pip_version' in py_info:
            pip_status = "✅" if py_info.get('pip_meets_requirement', False) else "⚠️ "
            print(f"  pip Version: {py_info['pip_version']} {pip_status} (Recommended: {REQUIREMENTS['pip']}+)")
        
        # Print package status
        print("\n📦 Package Status:")
        for pkg, info in self.results.get('packages', {}).items():
            if info.get('installed', False):
                status = "✅" if info.get('meets_requirement', False) else "⚠️ "
                print(f"  {pkg}: {info.get('version', 'N/A')} {status} (Required: {info.get('required', 'N/A')}+)")
            else:
                print(f"  {pkg}: ❌ Not installed (Required: {info.get('required', 'N/A')}+)")
        
        # Print optional packages
        if self.results.get('optional'):
            print("\n🔍 Optional Packages:")
            for pkg, info in self.results['optional'].items():
                status = "✅" if info.get('installed', False) else "◻️"
                version = f" ({info.get('version', '')})" if info.get('installed', False) else ""
                print(f"  {status} {pkg}{version}: {info.get('description', '')}")
        
        # Print directory status
        if self.results.get('directories'):
            print("\n📁 Directory Status:")
            for dir_name, info in self.results['directories'].items():
                status = "✅" if info.get('exists', False) and info.get('writable', False) else "⚠️ "
                if not info.get('exists', False):
                    status = "❌ (Does not exist)"
                elif not info.get('writable', False):
                    status = "⚠️  (Not writable)"
                print(f"  {status} {dir_name}/")
        
        # Print warnings and errors
        if self.results.get('warnings'):
            print("\n⚠️  Warnings:")
            for warning in self.results['warnings']:
                print(f"  • {warning}")
        
        if self.results.get('errors'):
            print("\n❌ Errors:")
            for error in self.results['errors']:
                print(f"  • {error}")
        
        # Print summary
        print("\n" + "="*50)
        if self.results.get('errors'):
            print("❌ Some requirements are not met. Please fix the errors above.")
        elif self.results.get('warnings'):
            print("⚠️  Some optional requirements are not met, but the application may still work.")
        else:
            print("✅ All requirements are met. You're good to go!")
        print("="*50 + "\n")
        
        return not bool(self.results.get('errors'))

def main():
    """Run system checks and print results."""
    checker = SystemChecker()
    checker.run_checks()
    success = checker.print_results()
    
    if not success:
        print("\nPlease install the missing dependencies and fix the issues above before running the application.")
        print("You can install the required packages using:")
        print("  pip install -r requirements.txt")
        print("\nFor GPU support, you may also need to install:")
        print("  pip install faiss-gpu torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
