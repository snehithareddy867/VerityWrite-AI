SAMPLES = {
    "Recruiter feedback (robotic)": dict(
        context="Recruiter feedback", tone="Professional",
        text=("The candidate, Asha Rao, scored 82/100 in Python and 74/100 in SQL on 8 October 2026. "
              "The candidate demonstrated a good understanding of Python fundamentals but needs further "
              "assessment in SQL query optimization. The candidate is recommended for a second technical interview.")),
    "Candidate email (robotic)": dict(
        context="Candidate email", tone="Polished",
        text=("Dear Rahul Mehta, I hope this email finds you well. We are pleased to inform you that you have been "
              "shortlisted for the Backend Developer position at Orbit Labs. Furthermore, your technical interview "
              "is scheduled for 14 October 2026 at 11:00 AM IST. Please do not hesitate to contact us should you "
              "require any further clarification.")),
    "Interview question (robotic)": dict(
        context="Interview question", tone="Conversational",
        text=("Can you please elaborate on your experience with Docker and Kubernetes in production environments? "
              "Furthermore, kindly describe a scenario in which you utilized CI/CD pipelines in order to deploy applications.")),
    "Already natural (skip-gate test)": dict(
        context="Recruiter feedback", tone="Conversational",
        text=("Asha scored 82/100 in Python and 74/100 in SQL on 8 October 2026. Python basics look solid, but SQL "
              "query optimization needs more work. I'd suggest a second technical interview.")),
}
