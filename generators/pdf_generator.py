from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    ListFlowable, ListItem, Image as ReportLabImage
)
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import io
import re
import matplotlib.pyplot as plt

def save_analysis_to_pdf(analysis_text, output_pdf_name, content_type='summary'):
    print(f"📄 Saving {content_type} analysis to {output_pdf_name}...")
    doc = SimpleDocTemplate(output_pdf_name, pagesize=A4,
                            rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    story = []
    
    styles = getSampleStyleSheet()
    
    # Enhanced styling for better presentation
    title_style = ParagraphStyle('Title', parent=styles['Heading1'],
                                fontSize=16, spaceAfter=12, textColor=colors.darkblue,
                                alignment=TA_LEFT)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'],
                                   fontSize=14, spaceAfter=8, textColor=colors.darkblue,
                                   spaceBefore=12)
    subheading_style = ParagraphStyle('SubHeading', parent=styles['Heading3'],
                                      fontSize=12, spaceAfter=6, textColor=colors.navy,
                                      spaceBefore=8)
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'],
                                spaceAfter=4, leading=14, alignment=TA_LEFT,
                                fontSize=10)
    bullet_style = ParagraphStyle('Bullet', parent=styles['Normal'],
                                  fontSize=10, leftIndent=15, spaceAfter=3,
                                  textColor=colors.black)
    emphasis_style = ParagraphStyle('Emphasis', parent=styles['Normal'],
                                   fontSize=10, spaceAfter=4, textColor=colors.darkgreen,
                                   fontName='Helvetica-Bold')

    if content_type == 'summary':
        _generate_summary_pdf(analysis_text, doc, story, title_style, heading_style, 
                             subheading_style, body_style, bullet_style, emphasis_style)
    elif content_type == 'equations':
        _generate_equations_pdf(analysis_text, doc, story, heading_style, 
                               subheading_style, body_style, bullet_style)

    try:
        doc.build(story)
        print(f"✅ Successfully created PDF: {output_pdf_name}")
    except Exception as e:
        print(f"❌ Error building the PDF: {e}")

def _generate_summary_pdf(analysis_text, doc, story, title_style, heading_style, 
                         subheading_style, body_style, bullet_style, emphasis_style):
    """Generate PDF for summary content"""
    story.append(Paragraph("Research Paper Summary", title_style))
    story.append(Spacer(1, 15))
    
    sections = analysis_text.split("## ")
    for section_index, section in enumerate(sections):
        if not section.strip():
            continue
            
        lines = section.strip().splitlines()
        if not lines:
            continue
            
        title = lines[0].strip()
        if title:
            story.append(Paragraph(title, heading_style))
            story.append(Spacer(1, 6))
        
        content_lines = []
        for line in lines[1:]:
            line = line.strip()
            if line and not line.startswith('---'):
                content_lines.append(line)
        
        if content_lines:
            current_paragraph = []
            bullet_items = []
            
            for line in content_lines:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('- ') or line.startswith('* ') or line.startswith('• '):
                    if current_paragraph:
                        story.append(Paragraph(' '.join(current_paragraph), body_style))
                        story.append(Spacer(1, 4))
                        current_paragraph = []
                    
                    clean_line = re.sub(r'^[-*•]\s*', '', line)
                    bullet_items.append(Paragraph(clean_line, bullet_style))
                
                elif line.startswith('**') and line.endswith('**'):
                    if bullet_items:
                        bullet_list = ListFlowable(bullet_items, bulletType='bullet')
                        story.append(bullet_list)
                        story.append(Spacer(1, 6))
                        bullet_items = []
                    
                    if current_paragraph:
                        story.append(Paragraph(' '.join(current_paragraph), body_style))
                        story.append(Spacer(1, 6))
                        current_paragraph = []
                    
                    subheading_text = line.replace('**', '').strip()
                    story.append(Paragraph(subheading_text, subheading_style))
                    story.append(Spacer(1, 4))
                
                else:
                    if bullet_items:
                        bullet_list = ListFlowable(bullet_items, bulletType='bullet')
                        story.append(bullet_list)
                        story.append(Spacer(1, 6))
                        bullet_items = []
                    
                    current_paragraph.append(line)
            
            if current_paragraph:
                story.append(Paragraph(' '.join(current_paragraph), body_style))
                story.append(Spacer(1, 6))
            
            if bullet_items:
                bullet_list = ListFlowable(bullet_items, bulletType='bullet')
                story.append(bullet_list)
                story.append(Spacer(1, 8))
        
        if section_index < len(sections) - 1:
            story.append(Spacer(1, 12))
            story.append(Paragraph("<hr/>", ParagraphStyle('HR', textColor=colors.lightgrey)))
            story.append(Spacer(1, 12))

def _generate_equations_pdf(analysis_text, doc, story, heading_style, 
                           subheading_style, body_style, bullet_style):
    """Generate PDF for equations content"""
    cleaned_text = re.sub(r'--- PAGE \d+ ---', '', analysis_text).strip()
    sections = re.split(r'\s*---\s*', cleaned_text)
    
    for section in sections:
        if not section.strip():
            continue
        
        equation_match = re.search(r"(.*?Equation:)\s*(\$\$.*?\$\$)\s*(.*)", section, re.DOTALL | re.IGNORECASE)
        
        if equation_match:
            title_text = equation_match.group(1).replace('###', '').replace('**', '').strip()
            latex_string = re.sub(r'^\$\$|\$\$$', '', equation_match.group(2)).strip()
            explanation_text = equation_match.group(3).strip()

            story.append(Paragraph(title_text, heading_style))
            story.append(Spacer(1, 6))

            try:
                fig = plt.figure(figsize=(8, 2))
                try:
                    plt.text(0.5, 0.5, f"${latex_string}$", usetex=True,
                             fontsize=14, va='center', ha='center')
                except Exception:
                    plt.text(0.5, 0.5, f"${latex_string}$", usetex=False,
                             fontsize=14, va='center', ha='center')
                
                plt.axis('off')
                
                buf = io.BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.2, dpi=300)
                plt.close(fig)
                buf.seek(0)

                img = ReportLabImage(ImageReader(buf), hAlign='CENTER')
                max_width = 400
                if img.imageWidth > max_width:
                    ratio = max_width / img.imageWidth
                    img.drawWidth = max_width
                    img.drawHeight = img.imageHeight * ratio
                
                story.append(img)
                story.append(Spacer(1, 12))
                
            except Exception as e:
                print(f"⚠️ Could not render LaTeX: {latex_string}. Error: {e}")
                story.append(Paragraph(f"<i>LaTeX Equation: {latex_string}</i>", body_style))
            
            explanation_lines = explanation_text.split('\n')
            bullet_items = []
            regular_lines = []
            
            for line in explanation_lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('*'):
                    bullet_items.append(Paragraph(line.strip(' *'), bullet_style))
                else:
                    regular_lines.append(line)
            
            if bullet_items:
                bullet_list = ListFlowable(bullet_items, bulletType='bullet')
                story.append(bullet_list)
                story.append(Spacer(1, 6))
            
            for line in regular_lines:
                story.append(Paragraph(line, body_style))
            
            story.append(Spacer(1, 12))
            
        else:
            for line in section.split('\n'):
                line = line.strip()
                if not line:
                    continue
                if line.startswith('###'):
                    story.append(Paragraph(line.replace('###', '').strip(), subheading_style))
                elif line.startswith('*'):
                    story.append(Paragraph("• " + line.strip(' *'), body_style))
                else:
                    story.append(Paragraph(line, body_style))
            story.append(Spacer(1, 12))