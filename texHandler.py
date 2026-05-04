import json
from typing import Dict, Any, cast
from jinja2 import Environment, BaseLoader


class TexToJsonNormalizer:
    def __init__(self, template_str: str | None = None):
        """
        Initialize TexToJsonNormalizer for LaTeX conversion.
        """

        self.env = Environment(
            loader=BaseLoader(),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )

        self.template = self.env.from_string(r"""
\documentclass[a4paper,10pt]{article}

% -------------------- PACKAGES --------------------
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{geometry}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{setspace}
\usepackage{multicol}
\usepackage{tabularx}

\geometry{letterpaper, margin=0.7in}
\setlist[itemize]{noitemsep,leftmargin=*}
\setstretch{1.05}
\hypersetup{hidelinks}
\setlength{\parindent}{0pt}
\pagestyle{empty}

% -------------------- SECTION FORMAT --------------------
\titleformat{\section}
{\large\bfseries}
{}
{0pt}
{}
[\titlerule]

\titlespacing*{\section}{0pt}{10pt}{6pt}

% -------------------- DOCUMENT --------------------
\begin{document}

% -------------------- HEADER --------------------
\begin{center}
{\LARGE \textbf{ {{ header["name"] }} }}\\[4pt]

{{ header["contact"][:3] | join(" \;|\; ") }} \\ 
{{ header["contact"][3:] | join(" \;|\; ") }}

\end{center}

% -------------------- SKILLS --------------------
\section{Skills}

\begin{center}
\begin{minipage}{0.95\textwidth}
\begin{tabularx}{\textwidth}{@{}>{\raggedright\arraybackslash\setlength{\parindent}{0pt}}X >{\raggedright\arraybackslash\setlength{\parindent}{0pt}}X@{}}

{% for i in range(0, skills|length, 2) %}
                                             
\begin{minipage}[t]{\linewidth}
\textbf{ {{- skills[i]["category"] }} }\\[-2pt]
{{ skills[i]["items"] | join(", ") }}
\end{minipage}
&
{% if i+1 < skills|length %}
\begin{minipage}[t]{\linewidth}
\textbf{ {{- skills[i+1]["category"] }} }\\[-2pt]
{{ skills[i+1]["items"] | join(", ") }}
\end{minipage}
{% endif %}
\\[8pt]

{% endfor %}

\end{tabularx}
\end{minipage}
\end{center}
% -------------------- EXPERIENCE --------------------
\section{Experience}

{% for job in experience %}
\textbf{ {{- job["company"] }} } \\
\textit{ {{ job["role"] }} } \hfill {{ job["duration"] }}
\begin{itemize}
{% for b in job["bullets"] %}
\item {{ b }}
{% endfor %}
\end{itemize}
\vspace{2pt}
{% endfor %}

% -------------------- PROJECTS --------------------
{% if projects %}
\section{Projects}

{% for proj in projects %}
\textbf{ {{- proj["name"] }} }
\begin{itemize}
{% for b in proj["bullets"] %}
\item {{ b }}
{% endfor %}
\end{itemize}
{% endfor %}
{% endif %}

% -------------------- EDUCATION --------------------
{% if education %}
\section{Education}

{% for e in education %}
\textbf{ {{- e["institution"] }} } \hfill {{ e["duration"] }} \\
\textit{ {{ e["degree"] }} } \\
{{ e["details"] }} \\[4pt]
{% endfor %}

{% endif %}
% -------------------- ACHIEVEMENTS --------------------
{% if achievements %}
\section{Achievements}

\begin{itemize}
{% for a in achievements %}
\item {{ a }}
{% endfor %}
\end{itemize}
{% endif %}

\end{document}
""")

    # -------------------- LATEX ESCAPE --------------------
    def _escape_latex(self, text: str) -> str:
        replacements = {
            "\\": r"\textbackslash{}",
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\textasciicircum{}",
            "–": "--",   # FIX
        	"—": "---",  # FIX
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        return text

    def _sanitize(self, data):
        if isinstance(data, dict):
            return {k: self._sanitize(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize(i) for i in data]
        elif isinstance(data, str):
            return self._escape_latex(data)
        return data

    # -------------------- JSON → LATEX --------------------
    def to_latex(self, data: dict[str, Any]) -> str:
        data = self._validate(data)
        clean_data = cast(dict[str, Any], self._sanitize(data))
        return self.template.render(**clean_data)

    # -------------------- PROMPT BUILDERS --------------------
    def _build_prompt(self, tex: str) -> str:
        return (
            "You are a LaTeX resume parser.\n"
            "INPUT:\n" + tex + "\n\n"
            "TASK:\n"
            "- Extract structured data into JSON.\n"
            "- Preserve all bullet points exactly.\n"
            "- Do NOT summarize or rewrite. **Extract all information strictly.**\n"
            "- Normalize sections into: header, skills, experience, projects, education, achievements.\n"
            "- Extract company, role, duration when possible.\n"
            "- If missing, use empty string.\n"
            "- Skills must be grouped into categories.\n\n"
            "OUTPUT:\n"
            "Return STRICT JSON only in this schema especially the keys:\n"
            '{ "header": { "name": "", "contact": [] }, '
            '"skills": [{ "category": "", "items": [] }], '
            '"experience": [{ "company": "", "role": "", "duration": "", "bullets": [] }], '
            '"projects": [{ "name": "", "bullets": [] }], '
            '"education": [{"institution": "","duration": "","degree": "","details": "GPA or CGPA if available, else empty"},],'
            '"achievements": [] }'
        )

    def _build_optimize_prompt(self, resume_json: str, jd_str: str) -> str:
        return (
            "You are optimizing a resume for a job description.\n\n"
            "INPUT:\n"
            "1) Job Description:\n" + jd_str + "\n\n"
            "2) Resume JSON:\n" + resume_json + "\n\n"
            "RULES:\n"
            "- Do NOT add new skills, tools, or experiences.\n"
            "- Do NOT fabricate metrics.\n"
            "- Preserve truth.\n"
            "- Keep bullets concise.\n\n"
            "TASK:\n"
            "- Align resume with job description.\n"
            "- Improve wording.\n"
            "- Reorder bullets by relevance.\n"
            "- Remove weak or irrelevant bullets.\n\n"
            "OUTPUT:\n"
            "Return FULL updated JSON only."
        )

    # -------------------- VALIDATION --------------------
    def _validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return {}

        data.setdefault("header", {"name": "", "contact": []})
        data.setdefault("skills", [])
        data.setdefault("experience", [])
        data.setdefault("projects", [])
        data.setdefault("education", [])
        data.setdefault("achievements", [])

        # enforce structure
        if not isinstance(data["header"], dict):
            data["header"] = {"name": "", "contact": []}

        data["header"].setdefault("name", "")
        data["header"].setdefault("contact", [])

        if not isinstance(data["skills"], list):
            data["skills"] = []

        for skill in data["skills"]:
            if isinstance(skill, dict):
                skill.setdefault("category", "")
                skill.setdefault("items", [])
                if not isinstance(skill["items"], list):
                    skill["items"] = []

        if not isinstance(data["experience"], list):
            data["experience"] = []

        for job in data["experience"]:
            if isinstance(job, dict):
                job.setdefault("company", "")
                job.setdefault("role", "")
                job.setdefault("duration", "")
                job.setdefault("bullets", [])
                if not isinstance(job["bullets"], list):
                    job["bullets"] = []

        if not isinstance(data["projects"], list):
            data["projects"] = []

        for proj in data["projects"]:
            if isinstance(proj, dict):
                proj.setdefault("name", "")
                proj.setdefault("bullets", [])
                if not isinstance(proj["bullets"], list):
                    proj["bullets"] = []

        if not isinstance(data["education"], list):
            data["education"] = []

        if not isinstance(data["achievements"], list):
            data["achievements"] = []

        return data