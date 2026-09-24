# scripts/run_public.ps1
conda activate atw-core
cd $PSScriptRoot\..
uvicorn public.api_public:app --host 127.0.0.1 --port 8000 --reload