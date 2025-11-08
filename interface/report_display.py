# © 2025 Numantic Solutions LLC
# MIT License
#
# Display the polciy report in Streamlit

import streamlit as st
import pandas as pd
import re
import json
from datetime import datetime

### Step 1.6. Set parameters
time_fmt = "%Y%m%d_%H%M%S"

def display_report(report_data: dict):
    """
    Displays the complete report dictionary content using Streamlit components.

    Args:
        report_data (dict): A dictionary containing the report structure
                            (title, summary, body, references).
    """

    st.set_page_config(layout="wide")

    # 1. Display the Title
    # The title contains Markdown (###), so we use st.markdown
    st.markdown(report_data.get('report_title', 'Report Title Not Found'))
    st.divider()

    # 2. Display the Executive Summary
    st.header("Executive Summary")
    st.write(report_data.get('report_executive_summary', 'Summary not available.'))

    st.divider()

    # 3. Display the Report Body
    # We use an expander to keep the main view clean, as requested.
    with st.expander("Expand to view Full Report Body", expanded=False):
        # st.markdown handles all internal Markdown formatting (headings, lists)
        # Check for common formatting issues
        if len(validate_markdown(markdown_content=report_data.get('report_body'))) == 0:
            st.markdown(report_data.get('report_body', 'Report body content not available.'))

        else:
            st.write(report_data.get('report_body', 'Report body content not available.'))
    st.divider()

    # 4. Display the References using a DataFrame
    st.header("References")

    references = report_data.get('report_references', [])

    if references:
        try:
            # Convert the list of dictionaries into a Pandas DataFrame for clean display
            df_references = pd.DataFrame(references)

            # Optional: Make URIs clickable if you want to use st.data_editor
            # For simplicity, we stick to st.dataframe which is sufficient.
            st.dataframe(df_references, use_container_width=True)
        except Exception as e:
            st.error(f"Could not format references data. Error: {e}")
            st.json(references) # Fallback to display raw JSON
    else:
        st.info("No references found for this report.")

def validate_markdown(markdown_content: str) -> list:
    """
    Checks for common Markdown formatting issues that could lead to poor rendering.

    Args:
        markdown_content: The string containing the Markdown text.

    Returns:
        A list of strings describing any formatting issues found.
    """
    issues = []
    lines = markdown_content.split('\n')

    # 1. Check for inconsistent or incorrectly spaced Headings
    # Pattern: Checks for lines starting with '##' or '###' (common in reports)
    # that are NOT immediately followed by a space, which is technically invalid MD.
    heading_pattern = re.compile(r'^(#+)(?=[A-Za-z0-9])')  # Matches ##I or ###A

    # 2. Check for non-standard List Item spacing (using non-breaking space or too many spaces)
    # Pattern: Checks for a list marker followed by non-standard whitespace (e.g., three spaces or a non-breaking space).
    # Standard is usually '* ' or '* ' (for indentation).
    # We flag the specific non-standard pattern: marker + a non-breaking space + three spaces
    list_spacing_pattern = re.compile(r'^[*-]\s*(\s{3,}|\u00A0)')  # Matches '* ' or '*\u00A0  '

    # 3. Check for incomplete bolding (unclosed ** or * across a line)
    # This check is less definitive but catches common AI errors.
    # It counts the total occurrences of '**' on a line. If odd, it's potentially unclosed.

    for i, line in enumerate(lines):
        line = line.strip()

        # Check 1: Heading Spacing
        if heading_pattern.match(line):
            issues.append(f"Line {i + 1}: Invalid heading spacing found (e.g., '###I.'). Needs a space after hashes.")

        # Check 2: List Spacing/Non-Breaking Space
        if line.startswith('*') or line.startswith('-'):
            # Check for the specific non-standard indentation observed (e.g., '*\u00A0   **Policy Setting...**')
            if list_spacing_pattern.match(line):
                issues.append(
                    f"Line {i + 1}: Non-standard list indentation or non-breaking space (`\\u00A0`) found. Recommend plain text.")

        # Check 3: Unclosed Bold/Emphasis (simple check)
        bold_count = line.count('**') + line.count('*')
        if bold_count % 2 != 0 and bold_count > 0:
            # We only flag if the issue isn't on a heading line, which can have odd counts.
            if not line.startswith('#'):
                issues.append(
                    f"Line {i + 1}: Odd number of bold/italic markers ('**' or '*') suggests unclosed formatting.")

    return issues


def format_download_content(messages: list) -> str:
    """
    Converts the session state messages into a single, structured string
    suitable copying into a rich text editor.

    Args:
        messages (list): st.session_state.messages list.

    Returns:
        str: The complete conversation formatted in Markdown.
    """
    export_content = [f"CCC Policy Assistant Conversation Export - {datetime.now().strftime(time_fmt)}\n"]

    for i, message in enumerate(messages):
        role = message["role"].capitalize()
        content = message["content"]

        # Add a clear section heading for each turn
        export_content.append(f"\n---\n\n Turn {i + 1}: {role} Message\n")

        if role == "Assistant":
            # If the content is the structured report (dictionary), embed the
            # contents using a modified version of the display_report logic.
            if isinstance(content, dict):
                report_data = content

                # 1. Title
                export_content.append("\nTitle\n")
                title = report_data.get('report_title', 'Report Title Not Found')
                export_content.append(clean_report_text(title))

                # 2. Executive Summary
                exe_sum = report_data.get('report_executive_summary', 'Summary not available.')
                export_content.append("\nExecutive Summary\n")
                export_content.append(clean_report_text(exe_sum))

                # 3. Report Body (Full Markdown content)
                full_body = report_data.get('report_body', 'Report body content not available.')
                export_content.append("\nFull Report Body\n")
                export_content.append(clean_report_text(full_body))

                # 4. References
                export_content.append("\References\n")
                references = report_data.get('report_references', [])
                if references:
                    # Format references into a readable Markdown list
                    ref_list = "\n".join([
                        f"Source: {ref.get('uri_text', 'N/A')}\n  URI: {ref.get('uri', 'N/A')}"
                        for ref in references
                    ])
                    export_content.append(ref_list)
                else:
                    export_content.append("No references found for this report.")

            else:
                # Fallback for simple assistant text messages
                export_content.append(content)

        else:
            # User messages are simple Markdown
            export_content.append(content)

    return "\n".join(export_content)


def clean_report_text(intext: str):
    """
    Function to clean markdown characters from report content text.
    :param intext:
    :return:
    """

    return intext.replace("*", "").replace("#", "").strip()
