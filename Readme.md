Resume Optimizer

A Python tool that uses AI to optimize your LaTeX resume against job descriptions. It parses your resume, analyzes the target job description, and generates an optimized version tailored to the role.

Features

- Parse LaTeX resumes and convert them to structured data
- Use OpenAI models to optimize resume content against job descriptions
- Generate optimized LaTeX resumes
- Compile to PDF with pdflatex
- Cache results to reduce API calls
- Support multiple input methods for job descriptions
- Rich terminal output with progress tracking

Prerequisites

- Python 3.10+
- OpenAI API key (set as OPENAI_API_KEY environment variable)
- pdflatex (for PDF compilation - part of MiKTeX or TeX Live)
- initexmf (comes with MiKTeX on Windows)

Setup Instructions

Quick Setup (Windows)

Run the setup script:

`setup.bat` in cmd or `cmd /c setup.bat` in powershell

This will automatically:
- Create a Python virtual environment
- Install all dependencies
- Create a .env file
- Optionally prompt for your OpenAI API key, or let you add it later

Manual Setup

1. Clone the repository

`git clone https://github.com/hemaangsood/ResumeOptimizer.git`

`cd ResumeOptimizer`

2. Create a virtual environment

`python -m venv venv`

On Windows:
`venv\Scripts\activate`

On macOS/Linux:
`source venv/bin/activate`

3. Install dependencies

`pip install -r req.txt`

4. Set up environment variables

Create a .env file in the project root:

`OPENAI_API_KEY=your_openai_api_key_here`

Replace your_openai_api_key_here with your actual OpenAI API key from https://platform.openai.com/api-keys

5. Prepare your resume

Place or update your LaTeX resume file. By default, the tool looks for Resume.tex in the project root.

Usage

Basic usage with a job description file:

`python resume_builder.py --jd-file path/to/job_description.txt`

Provide job description directly:

`python resume_builder.py --jd "Your job description text here"`

Pipe job description from a file:

`type job_description.txt | python resume_builder.py`

PowerShell equivalent:

`Get-Content job_description.txt | python resume_builder.py`

Specify custom resume and output directory:

`python resume_builder.py --jd-file jd.txt --resume-tex MyResume.tex --output-dir ./my_output`

Skip PDF compilation (generate LaTeX only):

`python resume_builder.py --jd-file jd.txt --skip-compile`

Interactive mode (if no job description provided):

`python resume_builder.py`

Command-line arguments:

`--jd TEXT`                Provide job description directly
`--jd-file PATH`           Path to job description file
`--resume-tex PATH`        Path to LaTeX resume (default: Resume.tex)
`--output-dir PATH`        Output directory for generated files (default: output/)
`--skip-compile`           Generate LaTeX but do not compile to PDF

Project Structure

cache.py                 SQLite-based caching for API responses
modelHandler.py         OpenAI API interaction and response handling
texHandler.py           LaTeX parsing and template rendering
resume_builder.py       Main application and CLI
Resume.tex              Your LaTeX resume source file
req.txt                 Python dependencies
output/                 Generated resume files and PDFs

How It Works

1. Parse Input: Reads your LaTeX resume and job description
2. AI Optimization: Uses OpenAI to analyze the job description and optimize resume content
3. Generate LaTeX: Creates an optimized LaTeX resume with tailored content
4. Compile PDF: Runs pdflatex to generate the final PDF
5. Cache: Stores results to avoid redundant API calls

Dependencies

Key packages:
- openai: OpenAI API client
- python-dotenv: Environment variable management
- rich: Beautiful terminal output
- jinja2: Template rendering for LaTeX
