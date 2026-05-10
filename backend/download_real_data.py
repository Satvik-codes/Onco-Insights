import os
import urllib.request
import tarfile
import zipfile
import shutil
from pathlib import Path

# Add a standard User-Agent to bypass 403 Forbidden errors on S3
opener = urllib.request.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')]
urllib.request.install_opener(opener)

# Paths
BASE_DIR = Path(__file__).parent
RAW_DIR = BASE_DIR / "data" / "raw"
EXPR_DIR = RAW_DIR / "expression"
CLIN_DIR = RAW_DIR / "clinical"
MUT_DIR = RAW_DIR / "mutation"

EXPR_DIR.mkdir(parents=True, exist_ok=True)
CLIN_DIR.mkdir(parents=True, exist_ok=True)
MUT_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = [
    {
        "name": "HGNC Approved Symbols",
        "url": "https://ftp.ebi.ac.uk/pub/databases/genenames/hgnc/tsv/hgnc_complete_set.txt",
        "dest": RAW_DIR / "hgnc_approved_symbols.txt",
        "extract": False
    },
    {
        "name": "TCGA Clinical Survival Data",
        "url": "https://pancanatlas.xenahubs.net/download/Survival_SupplementalTable_S1_20171025_xena_sp",
        "dest": CLIN_DIR / "TCGA_survival_data.txt",
        "extract": False
    },
    {
        "name": "BRCA Mutation Data",
        "url": "https://cbioportal-datahub.s3.amazonaws.com/brca_tcga_pan_can_atlas_2018.tar.gz",
        "dest": MUT_DIR / "brca_tcga.tar.gz",
        "extract": True,
        "extract_file": "data_mutations.txt",
        "final_name": "brca_mutations.txt"
    },
    {
        "name": "LUAD Mutation Data",
        "url": "https://cbioportal-datahub.s3.amazonaws.com/luad_tcga_pan_can_atlas_2018.tar.gz",
        "dest": MUT_DIR / "luad_tcga.tar.gz",
        "extract": True,
        "extract_file": "data_mutations.txt",
        "final_name": "luad_mutations.txt"
    },
    {
        "name": "COAD Mutation Data",
        "url": "https://cbioportal-datahub.s3.amazonaws.com/coadread_tcga_pan_can_atlas_2018.tar.gz",
        "dest": MUT_DIR / "coad_tcga.tar.gz",
        "extract": True,
        "extract_file": "data_mutations.txt",
        "final_name": "coad_mutations.txt"
    },
    {
        "name": "TCGA Expression Phenotype",
        "url": "https://toil-xena-hub.s3.us-east-1.amazonaws.com/download/TcgaTargetGtex_phenotype.txt.gz",
        "dest": EXPR_DIR / "TcgaTargetGtex_phenotype.txt.gz",
        "extract": False
    },
    {
        "name": "TCGA Expression TPM (WARNING: ~1.5GB DOWNLOAD)",
        "url": "https://toil-xena-hub.s3.us-east-1.amazonaws.com/download/TcgaTargetGtex_rsem_gene_tpm.gz",
        "dest": EXPR_DIR / "TcgaTargetGtex_rsem_gene_tpm.gz",
        "extract": False
    }
]

def download_file(url, dest_path):
    print(f"Downloading {url} \n -> {dest_path}")
    
    # Custom progress bar
    def reporthook(count, block_size, total_size):
        if total_size > 0:
            percent = int(count * block_size * 100 / total_size)
            mb_downloaded = (count * block_size) / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            print(f"\rProgress: {percent}% ({mb_downloaded:.1f} MB / {mb_total:.1f} MB)", end="")
        else:
            mb_downloaded = (count * block_size) / (1024 * 1024)
            print(f"\rProgress: {mb_downloaded:.1f} MB downloaded...", end="")

    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    with urllib.request.urlopen(req) as response:
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        count = 0
        with open(dest_path, 'wb') as out_file:
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                out_file.write(buffer)
                count += 1
                reporthook(count, block_size, total_size)
    print("\nDownload complete.\n")

def extract_maf(tar_path, target_file, final_path):
    print(f"Extracting {target_file} from {tar_path}...")
    with tarfile.open(tar_path, "r:gz") as tar:
        for member in tar.getmembers():
            if member.name.endswith(target_file):
                member.name = final_path.name # Flatten path
                tar.extract(member, final_path.parent)
                print(f"Extracted to {final_path}")
                break
    os.remove(tar_path)
    print("Cleaned up tar file.\n")

def main():
    print("=== Cancer Gene Copilot: Real Data Downloader ===")
    print("This script will download the actual TCGA datasets from UCSC Xena and cBioPortal.")
    print("Note: The expression matrix is massive (~1.5GB compressed). This may take a while depending on your internet connection.\n")
    
    # 1. Clear out mock data
    print("Cleaning up old processed mock data...")
    processed_dir = BASE_DIR / "data" / "processed"
    if processed_dir.exists():
        shutil.rmtree(processed_dir)
        print("Removed mock processed data.")
        
    print("\nStarting downloads...")
    for ds in DATASETS:
        print(f"--- Fetching: {ds['name']} ---")
        if not ds["dest"].exists():
            download_file(ds["url"], ds["dest"])
            if ds.get("extract"):
                final_file = ds["dest"].parent / ds["final_name"]
                extract_maf(ds["dest"], ds["extract_file"], final_file)
        else:
            print(f"File already exists at {ds['dest']}, skipping download.\n")
            
    print("=== All data downloaded successfully! ===")
    print("You can now run the preprocessing orchestrator to clean and process this real data:")
    print("python -m backend.preprocessing.run_all")

if __name__ == "__main__":
    main()
