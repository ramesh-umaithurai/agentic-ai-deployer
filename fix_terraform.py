#!/usr/bin/env python3
"""Quick script to fix Terraform configuration issues"""

import shutil
from pathlib import Path

def fix_terraform_files():
    """Fix duplicate Terraform provider configurations"""
    terraform_dir = Path("outputs/terraform")
    
    if not terraform_dir.exists():
        print("❌ No Terraform outputs directory found")
        return
    
    # Remove all existing Terraform files
    print("🧹 Cleaning up existing Terraform files...")
    for tf_file in terraform_dir.glob("*.tf"):
        tf_file.unlink()
        print(f"✅ Removed {tf_file.name}")
    
    # Remove Terraform state
    state_files = [
        terraform_dir / ".terraform",
        terraform_dir / ".terraform.lock.hcl", 
        terraform_dir / "terraform.tfstate",
        terraform_dir / "terraform.tfstate.backup"
    ]
    
    for state_file in state_files:
        if state_file.exists():
            if state_file.is_dir():
                shutil.rmtree(state_file)
            else:
                state_file.unlink()
            print(f"✅ Removed {state_file.name}")
    
    print("🎉 Terraform files cleaned. Run the agent again to generate fresh configurations.")

if __name__ == "__main__":
    fix_terraform_files()