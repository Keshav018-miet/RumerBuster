"""
build_presentation_pptx.py
==========================
Generates a polished, executive 8-slide widescreen PowerPoint presentation (.pptx)
for RumorBuster using python-pptx.
"""

import os
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = pptx.Presentation()
    # 16:9 Widescreen dimensions
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6] # blank layout

    # Color Palette
    COLOR_BG_DARK = RGBColor(15, 23, 42)       # Slate 900
    COLOR_BG_LIGHT = RGBColor(248, 250, 252)   # Slate 50
    COLOR_CARD_LIGHT = RGBColor(255, 255, 255) # Pure White
    COLOR_CARD_BORDER = RGBColor(226, 232, 240)# Slate 200
    COLOR_CARD_BORDER_ACCENT = RGBColor(203, 213, 225) # Slate 300

    COLOR_ACCENT_BLUE = RGBColor(37, 99, 235)  # Blue 600
    COLOR_ACCENT_CYAN = RGBColor(56, 189, 248) # Sky 400
    COLOR_ACCENT_EMERALD = RGBColor(16, 185, 129) # Emerald 500

    COLOR_TEXT_PRIMARY = RGBColor(15, 23, 42)  # Slate 900
    COLOR_TEXT_SECONDARY = RGBColor(71, 85, 105) # Slate 600
    COLOR_TEXT_MUTED = RGBColor(148, 163, 184) # Slate 400
    COLOR_TEXT_WHITE = RGBColor(255, 255, 255)

    def set_slide_background(slide, color):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = color

    def add_header(slide, section_tag, main_title, subtitle=""):
        # Section Tag
        tag_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.45), Inches(11.7), Inches(0.35))
        tf_tag = tag_box.text_frame
        tf_tag.word_wrap = True
        tf_tag.margin_left = tf_tag.margin_top = tf_tag.margin_right = tf_tag.margin_bottom = 0
        p_tag = tf_tag.paragraphs[0]
        p_tag.text = section_tag.upper()
        p_tag.font.size = Pt(10)
        p_tag.font.bold = True
        p_tag.font.color.rgb = COLOR_ACCENT_BLUE
        p_tag.font.name = "Segoe UI"

        # Main Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Inches(0.55))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = main_title
        p_title.font.size = Pt(22)
        p_title.font.bold = True
        p_title.font.color.rgb = COLOR_TEXT_PRIMARY
        p_title.font.name = "Segoe UI"

        # Subtitle
        if subtitle:
            sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.3), Inches(11.7), Inches(0.35))
            tf_sub = sub_box.text_frame
            tf_sub.word_wrap = True
            tf_sub.margin_left = tf_sub.margin_top = tf_sub.margin_right = tf_sub.margin_bottom = 0
            p_sub = tf_sub.paragraphs[0]
            p_sub.text = subtitle
            p_sub.font.size = Pt(11)
            p_sub.font.color.rgb = COLOR_TEXT_SECONDARY
            p_sub.font.name = "Segoe UI"

    def create_card(slide, left, top, width, height, title="", title_color=COLOR_TEXT_PRIMARY, bg_color=COLOR_CARD_LIGHT, border_color=COLOR_CARD_BORDER):
        # Card shape
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1)

        # Card Title
        if title:
            tb = slide.shapes.add_textbox(left + Inches(0.35), top + Inches(0.3), width - Inches(0.7), Inches(0.4))
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
            p = tf.paragraphs[0]
            p.text = title
            p.font.size = Pt(14)
            p.font.bold = True
            p.font.color.rgb = title_color
            p.font.name = "Segoe UI"
        return shape

    # =========================================================================
    # SLIDE 1: TITLE SLIDE (Dark Executive Theme)
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide1, COLOR_BG_DARK)

    # Accent decorative top strip
    strip = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.8), Inches(2.2), Inches(0.08))
    strip.fill.solid()
    strip.fill.fore_color.rgb = COLOR_ACCENT_CYAN
    strip.line.fill.background()

    # Category Pill
    pill = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.3), Inches(4.5), Inches(0.42))
    pill.fill.solid()
    pill.fill.fore_color.rgb = RGBColor(30, 41, 59)
    pill.line.color.rgb = RGBColor(51, 65, 85)
    pill_tf = pill.text_frame
    pill_p = pill_tf.paragraphs[0]
    pill_p.text = "AI-POWERED MULTIMEDIA FORENSICS & VERIFICATION"
    pill_p.font.size = Pt(9)
    pill_p.font.bold = True
    pill_p.font.color.rgb = COLOR_ACCENT_CYAN
    pill_p.font.name = "Segoe UI"
    pill_p.alignment = PP_ALIGN.CENTER

    # Title: RUMORBUSTER
    t_box = slide1.shapes.add_textbox(Inches(0.8), Inches(2.1), Inches(11.7), Inches(1.3))
    tf = t_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "RUMORBUSTER"
    p.font.size = Pt(54)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_WHITE
    p.font.name = "Segoe UI"

    # Subtitle
    sub_box = slide1.shapes.add_textbox(Inches(0.8), Inches(3.45), Inches(11.7), Inches(0.6))
    tf_sub = sub_box.text_frame
    tf_sub.word_wrap = True
    p_sub = tf_sub.paragraphs[0]
    p_sub.text = "Digital Content Verification & Multimedia Forensic Analysis Platform"
    p_sub.font.size = Pt(20)
    p_sub.font.color.rgb = RGBColor(203, 213, 225)
    p_sub.font.name = "Segoe UI"

    # Meta card block on slide 1
    card_y = Inches(4.5)
    meta_card = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), card_y, Inches(11.7), Inches(2.1))
    meta_card.fill.solid()
    meta_card.fill.fore_color.rgb = RGBColor(24, 34, 53)
    meta_card.line.color.rgb = RGBColor(51, 65, 85)

    meta_tb = slide1.shapes.add_textbox(Inches(1.2), card_y + Inches(0.25), Inches(10.9), Inches(1.6))
    meta_tf = meta_tb.text_frame
    meta_tf.word_wrap = True

    items = [
        ("Core Engineering:", "Python 3.11, Flask WSGI, PyTorch, Scikit-learn, Google Gemini 2.5 Flash (RAG)"),
        ("Computer Vision:", "Facenet-PyTorch (MTCNN 30% margin) + timm (EfficientNet-B7 Noisy Student DFDC winner)"),
        ("Live Deployments:", "Vercel Edge Serverless (Production) & Cloudflare Secure Tunnel (Live Daemon)"),
        ("GitHub Repository:", "https://github.com/Keshav018-miet/RumerBuster (branch: main)")
    ]

    for i, (k, v) in enumerate(items):
        p_item = meta_tf.paragraphs[0] if i == 0 else meta_tf.add_paragraph()
        run1 = p_item.add_run()
        run1.text = f"{k}  "
        run1.font.bold = True
        run1.font.size = Pt(11)
        run1.font.color.rgb = COLOR_ACCENT_CYAN
        run1.font.name = "Segoe UI"

        run2 = p_item.add_run()
        run2.text = v
        run2.font.size = Pt(11)
        run2.font.color.rgb = RGBColor(241, 245, 249)
        run2.font.name = "Segoe UI"
        p_item.space_after = Pt(6)

    # =========================================================================
    # SLIDE 2: THE PROBLEM & THE SOLUTION
    # =========================================================================
    slide2 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide2, COLOR_BG_LIGHT)
    add_header(slide2, "01. Problem & Objective", "The Disinformation Crisis & Our Core Solution",
               "Why automated multi-modal verification is urgently required for digital integrity.")

    # Left Card: Problem
    create_card(slide2, Inches(0.8), Inches(1.8), Inches(5.65), Inches(5.1),
                "The Disinformation Landscape", RGBColor(220, 38, 38))
    tb_p = slide2.shapes.add_textbox(Inches(1.15), Inches(2.4), Inches(5.0), Inches(4.3))
    tf_p = tb_p.text_frame
    tf_p.word_wrap = True

    prob_bullets = [
        ("Viral Misinformation Spread: ", "False news and deceptive claims travel 6x faster than verified truth across social media channels."),
        ("Proliferation of Synthetic Media: ", "Accessible AI deepfakes and generative imaging make digital manipulation indistinguishable to the human eye."),
        ("Manual Fact-Checking Bottleneck: ", "Traditional journalism takes hours or days to verify breaking events, leaving public safety vulnerable."),
        ("Static Model Blindness: ", "Standard NLP classifiers trained on static datasets hallucinate or fail entirely on real-time breaking events.")
    ]
    for i, (b_title, b_desc) in enumerate(prob_bullets):
        p_b = tf_p.paragraphs[0] if i == 0 else tf_p.add_paragraph()
        r1 = p_b.add_run()
        r1.text = "- " + b_title
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = COLOR_TEXT_PRIMARY
        r1.font.name = "Segoe UI"
        r2 = p_b.add_run()
        r2.text = b_desc
        r2.font.size = Pt(10)
        r2.font.color.rgb = COLOR_TEXT_SECONDARY
        r2.font.name = "Segoe UI"
        p_b.space_after = Pt(12)

    # Right Card: Solution
    create_card(slide2, Inches(6.85), Inches(1.8), Inches(5.65), Inches(5.1),
                "The RumorBuster Mission", COLOR_ACCENT_BLUE)
    tb_s = slide2.shapes.add_textbox(Inches(7.2), Inches(2.4), Inches(5.0), Inches(4.3))
    tf_s = tb_s.text_frame
    tf_s.word_wrap = True

    sol_bullets = [
        ("Automated Multi-Modal Forensics: ", "Verifies text statements, live web claims, facial images, and file tampering in under 3 seconds."),
        ("Concurrent RAG Fact-Checking: ", "Queries 5 live news services simultaneously with strict 24-48h recency filtering and Gemini 2.5 Flash synthesis."),
        ("Kaggle DFDC-Winning Vision: ", "Employs MTCNN face extraction with 30% margin expansion and EfficientNet-B7 classification."),
        ("Auditable Chain of Custody: ", "Issues cryptographic SHA-256 and perceptual pHash forensic reports with immutable UUID records.")
    ]
    for i, (b_title, b_desc) in enumerate(sol_bullets):
        p_b = tf_s.paragraphs[0] if i == 0 else tf_s.add_paragraph()
        r1 = p_b.add_run()
        r1.text = "- " + b_title
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = COLOR_TEXT_PRIMARY
        r1.font.name = "Segoe UI"
        r2 = p_b.add_run()
        r2.text = b_desc
        r2.font.size = Pt(10)
        r2.font.color.rgb = COLOR_TEXT_SECONDARY
        r2.font.name = "Segoe UI"
        p_b.space_after = Pt(12)

    # =========================================================================
    # SLIDE 3: SYSTEM ARCHITECTURE & WORKFLOW PIPELINE
    # =========================================================================
    slide3 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide3, COLOR_BG_LIGHT)
    add_header(slide3, "02. Architecture & Pipeline", "Modular Multi-Tier Forensic Engineering",
               "End-to-end request lifecycle from multi-modal input to cryptographic audit report.")

    card_w = Inches(3.68)
    card_h = Inches(5.1)
    card_top = Inches(1.8)

    # Col 1: Presentation & Routing
    create_card(slide3, Inches(0.8), card_top, card_w, card_h, "1. Ingestion & Security", COLOR_ACCENT_BLUE)
    tb_c1 = slide3.shapes.add_textbox(Inches(1.05), card_top + Inches(0.8), card_w - Inches(0.5), card_h - Inches(1.0))
    tf_c1 = tb_c1.text_frame
    tf_c1.word_wrap = True
    c1_items = [
        ("Executive UI: ", "Clean, responsive slate/charcoal interface built with HTML5, CSS3 & Jinja2."),
        ("Flask WSGI Server: ", "Python backend managing routing, session cookies, and API controllers."),
        ("Security Guards: ", "@login_required decorators, PBKDF2 password hashing, and 50MB payload limits."),
        ("Sanitization: ", "secure_filename filtering and strict extension whitelisting (PNG, JPG, MP4).")
    ]
    for i, (k, v) in enumerate(c1_items):
        p = tf_c1.paragraphs[0] if i == 0 else tf_c1.add_paragraph()
        r1 = p.add_run()
        r1.text = k
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = COLOR_TEXT_PRIMARY
        r2 = p.add_run()
        r2.text = v
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = COLOR_TEXT_SECONDARY
        p.space_after = Pt(10)

    # Col 2: Analytical Engines
    create_card(slide3, Inches(4.82), card_top, card_w, card_h, "2. Forensic Engines", RGBColor(147, 51, 234))
    tb_c2 = slide3.shapes.add_textbox(Inches(5.07), card_top + Inches(0.8), card_w - Inches(0.5), card_h - Inches(1.0))
    tf_c2 = tb_c2.text_frame
    tf_c2.word_wrap = True
    c2_items = [
        ("NLP Text Classifier: ", "TF-IDF (5k features) + Logistic Regression scoring lexical authenticity."),
        ("Live RAG Engine: ", "ThreadPoolExecutor concurrently querying 5 live news APIs (Google News, NewsAPI, Inshorts)."),
        ("Gemini 2.5 Flash: ", "Evaluates retrieved web evidence with rigid JSON schema consensus."),
        ("Computer Vision: ", "MTCNN face extraction (30% margin) + EfficientNet-B7 deepfake detection.")
    ]
    for i, (k, v) in enumerate(c2_items):
        p = tf_c2.paragraphs[0] if i == 0 else tf_c2.add_paragraph()
        r1 = p.add_run()
        r1.text = k
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = COLOR_TEXT_PRIMARY
        r2 = p.add_run()
        r2.text = v
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = COLOR_TEXT_SECONDARY
        p.space_after = Pt(10)

    # Col 3: Storage & Audit
    create_card(slide3, Inches(8.84), card_top, card_w, card_h, "3. Storage & Audit", COLOR_ACCENT_EMERALD)
    tb_c3 = slide3.shapes.add_textbox(Inches(9.09), card_top + Inches(0.8), card_w - Inches(0.5), card_h - Inches(1.0))
    tf_c3 = tb_c3.text_frame
    tf_c3.word_wrap = True
    c3_items = [
        ("SHA-256 Hashing: ", "Bit-exact cryptographic signature calculation for digital file verification."),
        ("Perceptual pHash: ", "DCT-based visual structure footprint tracking localized manipulation."),
        ("EXIF Forensics: ", "Camera metadata, timestamp, GPS, and software editing signatures."),
        ("Chain of Custody: ", "Immutable SQLite audit logs tagged with UUIDv4, timestamps, and confidence ratings.")
    ]
    for i, (k, v) in enumerate(c3_items):
        p = tf_c3.paragraphs[0] if i == 0 else tf_c3.add_paragraph()
        r1 = p.add_run()
        r1.text = k
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = COLOR_TEXT_PRIMARY
        r2 = p.add_run()
        r2.text = v
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = COLOR_TEXT_SECONDARY
        p.space_after = Pt(10)

    # =========================================================================
    # SLIDE 4: REAL-TIME NEWS & MULTI-SOURCE RAG
    # =========================================================================
    slide4 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide4, COLOR_BG_LIGHT)
    add_header(slide4, "03. Text & News Verification", "Multi-Source RAG & Consensus Scoring Engine",
               "Eliminating LLM hallucinations by coupling real-time retrieval with structured generative AI.")

    create_card(slide4, Inches(0.8), Inches(1.8), Inches(5.65), Inches(5.1),
                "NLP Classifier (Static Baseline)", COLOR_TEXT_PRIMARY)
    tb_m1 = slide4.shapes.add_textbox(Inches(1.15), Inches(2.4), Inches(5.0), Inches(4.3))
    tf_m1 = tb_m1.text_frame
    tf_m1.word_wrap = True
    m1_points = [
        ("Feature Extraction: ", "Text is sanitized, stripped of stop words, and mapped into sparse TF-IDF n-grams (1, 2) up to 5,000 features."),
        ("Logistic Regression: ", "Computes probabilistic confidence via sigmoid distribution in ~2.4 milliseconds."),
        ("Explainable Scoring: ", "Provides transparent weights for feature words rather than uninterpretable black-box decisions."),
        ("Official Channel Whitelist: ", "Cross-checks handles against trusted sources (PIB, ISRO, DRDO) to prevent false alerts on official communiques.")
    ]
    for i, (k, v) in enumerate(m1_points):
        p = tf_m1.paragraphs[0] if i == 0 else tf_m1.add_paragraph()
        r1 = p.add_run()
        r1.text = "- " + k
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = COLOR_TEXT_PRIMARY
        r2 = p.add_run()
        r2.text = v
        r2.font.size = Pt(10)
        r2.font.color.rgb = COLOR_TEXT_SECONDARY
        p.space_after = Pt(12)

    create_card(slide4, Inches(6.85), Inches(1.8), Inches(5.65), Inches(5.1),
                "Live Web Search (Multi-Source RAG)", COLOR_ACCENT_BLUE)
    tb_m2 = slide4.shapes.add_textbox(Inches(7.2), Inches(2.4), Inches(5.0), Inches(4.3))
    tf_m2 = tb_m2.text_frame
    tf_m2.word_wrap = True
    m2_points = [
        ("spaCy Named Entity Recognition: ", "Identifies core entities (ORG, GPE, PERSON, EVENT) with automated fallback cleaning."),
        ("Concurrent News Ingestion: ", "ThreadPoolExecutor queries PyGoogleNews, NewsAPI, Inshorts endpoints, and Open-News in parallel."),
        ("Recency & Deduplication: ", "Enforces strict 24-48h recency filters and removes duplicate articles via normalized string similarity."),
        ("Gemini 2.5 Flash Synthesis: ", "Evaluates claims strictly against retrieved articles, returning status, confidence (0-100), and clickable citations."),
        ("Breaking News Override: ", "Corroborated mainstream coverage overrides offline static alerts to eliminate false positives.")
    ]
    for i, (k, v) in enumerate(m2_points):
        p = tf_m2.paragraphs[0] if i == 0 else tf_m2.add_paragraph()
        r1 = p.add_run()
        r1.text = "- " + k
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = COLOR_TEXT_PRIMARY
        r2 = p.add_run()
        r2.text = v
        r2.font.size = Pt(10)
        r2.font.color.rgb = COLOR_TEXT_SECONDARY
        p.space_after = Pt(10)

    # =========================================================================
    # SLIDE 5: AI DEEPFAKE DETECTION & COMPUTER VISION
    # =========================================================================
    slide5 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide5, COLOR_BG_LIGHT)
    add_header(slide5, "04. Computer Vision Forensics", "Neural Deepfake Detection & Facial Analysis",
               "Integrating Kaggle DFDC 1st-place winning architecture with MTCNN boundary extraction.")

    create_card(slide5, Inches(0.8), Inches(1.8), Inches(5.65), Inches(5.1),
                "MTCNN Face Extraction (30% Margin)", RGBColor(147, 51, 234))
    tb_df1 = slide5.shapes.add_textbox(Inches(1.15), Inches(2.4), Inches(5.0), Inches(4.3))
    tf_df1 = tb_df1.text_frame
    tf_df1.word_wrap = True
    df1_points = [
        ("DFDC Winning Foundation: ", "Faithfully implements Selim Seferbekov's 1st-place solution from Kaggle's Deepfake Detection Challenge."),
        ("Multi-Stage Face Detection: ", "facenet-pytorch MTCNN detects facial landmarks, selects the largest face, and outputs bounding coordinates."),
        ("Why the 30% Margin Expansion? ", "Deepfake generators blend synthetic faces into original footage, leaving seam artifacts along jawlines, ears, and hair.\n\nTight bounding boxes crop these seams out! Adding a 30% margin on all 4 sides captures the critical artifact boundaries needed for classification.")
    ]
    for i, (k, v) in enumerate(df1_points):
        p = tf_df1.paragraphs[0] if i == 0 else tf_df1.add_paragraph()
        r1 = p.add_run()
        r1.text = "- " + k
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = COLOR_TEXT_PRIMARY
        r2 = p.add_run()
        r2.text = v
        r2.font.size = Pt(10)
        r2.font.color.rgb = COLOR_TEXT_SECONDARY
        p.space_after = Pt(12)

    create_card(slide5, Inches(6.85), Inches(1.8), Inches(5.65), Inches(5.1),
                "EfficientNet-B7 & Video Forensics", COLOR_ACCENT_BLUE)
    tb_df2 = slide5.shapes.add_textbox(Inches(7.2), Inches(2.4), Inches(5.0), Inches(4.3))
    tf_df2 = tb_df2.text_frame
    tf_df2.word_wrap = True
    df2_points = [
        ("EfficientNet-B7 Backbone: ", "Constructed via timm (tf_efficientnet_b7_ns) pre-trained with ImageNet Noisy Student self-training."),
        ("High-Resolution Tensor Input: ", "Resizes face crops to 380x380 resolution with ImageNet mean/std normalization."),
        ("Inference Service API: ", "deepfake_api.py accepts file paths, PIL images, or byte streams, outputting is_deepfake, confidence_score, and bounding boxes."),
        ("Video Temporal Forensics: ", "Decodes video frames, inspects facial regions sequentially, and tracks perceptual hash drift across frames to uncover splicing.")
    ]
    for i, (k, v) in enumerate(df2_points):
        p = tf_df2.paragraphs[0] if i == 0 else tf_df2.add_paragraph()
        r1 = p.add_run()
        r1.text = "- " + k
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = COLOR_TEXT_PRIMARY
        r2 = p.add_run()
        r2.text = v
        r2.font.size = Pt(10)
        r2.font.color.rgb = COLOR_TEXT_SECONDARY
        p.space_after = Pt(12)

    # =========================================================================
    # SLIDE 6: CRYPTOGRAPHIC INTEGRITY & CHAIN OF CUSTODY
    # =========================================================================
    slide6 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide6, COLOR_BG_LIGHT)
    add_header(slide6, "05. Cryptographic Forensics", "Dual-Layer Integrity & Auditable Evidence",
               "Combining mathematical bit-exact hashing with perceptual frequency footprints.")

    create_card(slide6, Inches(0.8), Inches(1.8), Inches(5.65), Inches(5.1),
                "Cryptographic vs. Perceptual Hashing", COLOR_TEXT_PRIMARY)
    tb_cr1 = slide6.shapes.add_textbox(Inches(1.15), Inches(2.4), Inches(5.0), Inches(4.3))
    tf_cr1 = tb_cr1.text_frame
    tf_cr1.word_wrap = True
    cr1_points = [
        ("SHA-256 (Bit-Level Identity): ", "A 256-bit cryptographic digest. The avalanche effect guarantees that modifying a single bit changes the entire hash. Proves files are unaltered."),
        ("Perceptual Hashing (pHash): ", "Computes Discrete Cosine Transform (DCT) frequency coefficients representing visual structure. Invariant to benign compression/resizing, but exposes localized tampering."),
        ("Complementary Defense: ", "SHA-256 proves exact file identity; pHash proves whether two differently compressed images depict the exact same scene.")
    ]
    for i, (k, v) in enumerate(cr1_points):
        p = tf_cr1.paragraphs[0] if i == 0 else tf_cr1.add_paragraph()
        r1 = p.add_run()
        r1.text = "- " + k
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = COLOR_TEXT_PRIMARY
        r2 = p.add_run()
        r2.text = v
        r2.font.size = Pt(10)
        r2.font.color.rgb = COLOR_TEXT_SECONDARY
        p.space_after = Pt(14)

    create_card(slide6, Inches(6.85), Inches(1.8), Inches(5.65), Inches(5.1),
                "EXIF Extraction & Chain of Custody", COLOR_ACCENT_EMERALD)
    tb_cr2 = slide6.shapes.add_textbox(Inches(7.2), Inches(2.4), Inches(5.0), Inches(4.3))
    tf_cr2 = tb_cr2.text_frame
    tf_cr2.word_wrap = True
    cr2_points = [
        ("EXIF Metadata Forensics: ", "Pillow extracts embedded hardware tags: camera make/model, lens aperture, shutter speed, timestamp, and GPS coordinates."),
        ("Tampering Signature Detection: ", "Detects software editing traces (e.g. Adobe Photoshop, GIMP, or Canvas editing fingerprints) within metadata headers."),
        ("Immutable Chain of Custody: ", "Every analysis is registered in SQLite with an immutable UUIDv4, investigator identity, timestamps, hashes, and classification metrics."),
        ("Enterprise PDF Export: ", "Generates auditable, timestamped forensic reports suitable for legal review and organizational compliance.")
    ]
    for i, (k, v) in enumerate(cr2_points):
        p = tf_cr2.paragraphs[0] if i == 0 else tf_cr2.add_paragraph()
        r1 = p.add_run()
        r1.text = "- " + k
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = COLOR_TEXT_PRIMARY
        r2 = p.add_run()
        r2.text = v
        r2.font.size = Pt(10)
        r2.font.color.rgb = COLOR_TEXT_SECONDARY
        p.space_after = Pt(12)

    # =========================================================================
    # SLIDE 7: TECHNICAL STACK & DEPLOYMENT ENGINEERING
    # =========================================================================
    slide7 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide7, COLOR_BG_LIGHT)
    add_header(slide7, "06. DevOps & Infrastructure", "Production Engineering & Cold-Boot Optimization",
               "Architectural optimizations enabling serverless deployment and edge delivery.")

    create_card(slide7, Inches(0.8), Inches(1.8), Inches(5.65), Inches(5.1),
                "Production Technology Stack", COLOR_TEXT_PRIMARY)
    tb_t1 = slide7.shapes.add_textbox(Inches(1.15), Inches(2.4), Inches(5.0), Inches(4.3))
    tf_t1 = tb_t1.text_frame
    tf_t1.word_wrap = True
    t1_points = [
        ("Backend & Web Framework: ", "Python 3.11+, Flask WSGI microframework, Jinja2 templating, and ThreadPoolExecutor."),
        ("Machine Learning & AI: ", "PyTorch, timm, facenet-pytorch (MTCNN), Scikit-learn, and Google GenAI SDK (Gemini 2.5 Flash)."),
        ("Storage & Database: ", "SQLite3 (WAL mode) with parameterized queries for zero SQL-injection vulnerability."),
        ("Frontend Design System: ", "Custom executive slate/charcoal CSS3 design system with mobile-first viewport scaling and floating card components.")
    ]
    for i, (k, v) in enumerate(t1_points):
        p = tf_t1.paragraphs[0] if i == 0 else tf_t1.add_paragraph()
        r1 = p.add_run()
        r1.text = "- " + k
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = COLOR_TEXT_PRIMARY
        r2 = p.add_run()
        r2.text = v
        r2.font.size = Pt(10)
        r2.font.color.rgb = COLOR_TEXT_SECONDARY
        p.space_after = Pt(12)

    create_card(slide7, Inches(6.85), Inches(1.8), Inches(5.65), Inches(5.1),
                "Serverless & Edge Optimization", COLOR_ACCENT_BLUE)
    tb_t2 = slide7.shapes.add_textbox(Inches(7.2), Inches(2.4), Inches(5.0), Inches(4.3))
    tf_t2 = tb_t2.text_frame
    tf_t2.word_wrap = True
    t2_points = [
        ("Solving Serverless Cold-Boot: ", "Heavy libraries (PyTorch, spaCy, timm) exceeded Vercel's 10s limit. We implemented Lazy Singleton Loading, dropping cold boot from >7.5s to 1.1s."),
        ("Vercel Edge CDN Pipeline: ", "Configured @vercel/static builders with check: true rules; stylesheets and assets are served globally via CDN with 0ms serverless delay."),
        ("Cloudflare Tunnel Daemon: ", "Continuous background cloudflared daemon exposes local development securely over HTTPS without port forwarding."),
        ("Authentication & Access: ", "PBKDF2 salted password hashing, HTTP-only SameSite session cookies, and @login_required endpoint protection.")
    ]
    for i, (k, v) in enumerate(t2_points):
        p = tf_t2.paragraphs[0] if i == 0 else tf_t2.add_paragraph()
        r1 = p.add_run()
        r1.text = "- " + k
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = COLOR_TEXT_PRIMARY
        r2 = p.add_run()
        r2.text = v
        r2.font.size = Pt(10)
        r2.font.color.rgb = COLOR_TEXT_SECONDARY
        p.space_after = Pt(10)

    # =========================================================================
    # SLIDE 8: IMPACT, PERFORMANCE & FUTURE ROADMAP
    # =========================================================================
    slide8 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide8, COLOR_BG_LIGHT)
    add_header(slide8, "07. Benchmarks & Roadmap", "System Metrics, Target Impact & Future Vision",
               "Empirical benchmarks, stakeholder benefits, and next-generation research roadmap.")

    # Top KPI Banner
    top_banner = slide8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.75), Inches(11.7), Inches(1.2))
    top_banner.fill.solid()
    top_banner.fill.fore_color.rgb = COLOR_CARD_LIGHT
    top_banner.line.color.rgb = COLOR_CARD_BORDER

    # KPI columns inside banner
    kpis = [
        ("2.4 ms", "NLP Text Inference Latency"),
        ("1.8 - 2.4 s", "Multi-Source RAG Query"),
        ("320 ms", "GPU Deepfake Detection"),
        ("1.1 s", "Vercel Cold-Boot Time")
    ]
    col_w = Inches(11.7 / 4.0)
    for i, (val, label) in enumerate(kpis):
        kpi_x = Inches(0.8) + i * col_w
        tb_kpi = slide8.shapes.add_textbox(kpi_x, Inches(1.85), col_w, Inches(1.0))
        tf_kpi = tb_kpi.text_frame
        tf_kpi.word_wrap = True
        p1 = tf_kpi.paragraphs[0]
        p1.text = val
        p1.font.size = Pt(22)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_ACCENT_BLUE
        p1.font.name = "Segoe UI"
        p1.alignment = PP_ALIGN.CENTER

        p2 = tf_kpi.add_paragraph()
        p2.text = label
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = COLOR_TEXT_SECONDARY
        p2.font.name = "Segoe UI"
        p2.alignment = PP_ALIGN.CENTER

    # Bottom Left: Target Stakeholders
    create_card(slide8, Inches(0.8), Inches(3.15), Inches(5.65), Inches(3.75),
                "Target Stakeholders & Impact", COLOR_TEXT_PRIMARY)
    tb_stk = slide8.shapes.add_textbox(Inches(1.15), Inches(3.75), Inches(5.0), Inches(3.0))
    tf_stk = tb_stk.text_frame
    tf_stk.word_wrap = True
    stk_items = [
        ("Cyber Forensic Cells & Police: ", "Verifiable chain-of-custody reports for evidence intake and legal prosecution."),
        ("Journalists & Fact-Checkers: ", "Rapid cross-checking of breaking viral claims against verified tier-1 news sources."),
        ("General Public & Researchers: ", "Self-service verification of social media rumors, deepfake videos, and forged documents.")
    ]
    for i, (k, v) in enumerate(stk_items):
        p = tf_stk.paragraphs[0] if i == 0 else tf_stk.add_paragraph()
        r1 = p.add_run()
        r1.text = "- " + k
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = COLOR_TEXT_PRIMARY
        r2 = p.add_run()
        r2.text = v
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = COLOR_TEXT_SECONDARY
        p.space_after = Pt(10)

    # Bottom Right: Future Roadmap
    create_card(slide8, Inches(6.85), Inches(3.15), Inches(5.65), Inches(3.75),
                "Next-Generation Roadmap", COLOR_ACCENT_BLUE)
    tb_rdm = slide8.shapes.add_textbox(Inches(7.2), Inches(3.75), Inches(5.0), Inches(3.0))
    tf_rdm = tb_rdm.text_frame
    tf_rdm.word_wrap = True
    rdm_items = [
        ("Audio Deepfake Detection: ", "Integrating wav2vec 2.0 and Whisper models to detect synthetic voice clones and forged speech."),
        ("Browser Extension: ", "One-click right-click verification extension directly on Twitter/X, WhatsApp Web, and Reddit."),
        ("Decentralized Hash Ledger: ", "Anchoring forensic hash proofs to public blockchain networks (Polygon) for permanent public tamper-evidence.")
    ]
    for i, (k, v) in enumerate(rdm_items):
        p = tf_rdm.paragraphs[0] if i == 0 else tf_rdm.add_paragraph()
        r1 = p.add_run()
        r1.text = "- " + k
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = COLOR_TEXT_PRIMARY
        r2 = p.add_run()
        r2.text = v
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = COLOR_TEXT_SECONDARY
        p.space_after = Pt(10)

    output_path = "RumorBuster_Project_Presentation.pptx"
    prs.save(output_path)
    print(f"Presentation saved successfully as {output_path}")
    return output_path

if __name__ == '__main__':
    create_presentation()
