"""Claude Code style dark theme for jojo-code TUI - Textual 8.x compatible"""

COLORS = {
    "bg_primary": "#0d0d0d",
    "bg_secondary": "#171717",
    "bg_tertiary": "#262626",
    "bg_hover": "#303030",
    "border": "#333333",
    "border_focus": "#a855f7",
    "text_primary": "#f5f5f5",
    "text_secondary": "#a3a3a3",
    "text_muted": "#737373",
    "accent_purple": "#a855f7",
    "accent_purple_dim": "#7c3aed",
    "accent_blue": "#3b82f6",
    "accent_green": "#22c55e",
    "accent_red": "#ef4444",
    "accent_yellow": "#eab308",
    "accent_orange": "#f97316",
}

CSS = f"""
Screen {{
    background: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
}}

#header {{
    height: 3;
    background: {COLORS['bg_secondary']};
    border-bottom: solid {COLORS['border']};
}}

#header-title {{
    color: {COLORS['text_primary']};
    padding-left: 1;
}}

#header-mode {{
    color: {COLORS['accent_purple']};
    padding-left: 1;
}}

#header-status {{
    color: {COLORS['text_muted']};
}}

#header-spacer {{
    width: 1fr;
}}

#header-conn {{
    padding-right: 1;
}}

#sidebar {{
    width: 26;
    background: {COLORS['bg_secondary']};
    border-right: solid {COLORS['border']};
}}

.sidebar-section {{
    color: {COLORS['text_muted']};
    text-style: bold;
    padding-top: 1;
    padding-left: 1;
}}

.sidebar-item {{
    padding-top: 0;
    padding-bottom: 0;
    padding-left: 2;
}}

.sidebar-item:hover {{
    background: {COLORS['bg_hover']};
}}

.sidebar-item.active {{
    background: {COLORS['accent_purple']};
    color: {COLORS['text_primary']};
}}

.placeholder {{
    color: {COLORS['text_muted']};
    text-style: italic;
}}

#chat-wrapper {{
    width: 1fr;
}}

#chat {{
    height: 1fr;
    padding: 1;
    background: {COLORS['bg_primary']};
}}

.message-user {{
    background: {COLORS['accent_blue']};
    color: #ffffff;
    padding-top: 8;
    padding-bottom: 8;
    padding-left: 12;
    padding-right: 12;
    margin-top: 4;
    margin-bottom: 4;
    max-width: 75%;
    width: auto;
}}

.message-assistant {{
    background: {COLORS['bg_tertiary']};
    border: solid {COLORS['border']};
    padding-top: 8;
    padding-bottom: 8;
    padding-left: 12;
    padding-right: 12;
    margin-top: 4;
    margin-bottom: 4;
    max-width: 85%;
    width: auto;
}}

.message-tool {{
    background: {COLORS['bg_secondary']};
    border: solid {COLORS['border']};
    padding-top: 4;
    padding-bottom: 4;
    padding-left: 10;
    padding-right: 10;
    margin-top: 2;
    margin-bottom: 2;
    max-width: 85%;
    color: {COLORS['accent_orange']};
}}

.loading-dots {{
    color: {COLORS['accent_purple']};
    text-style: bold;
}}

#input-area {{
    height: auto;
    min-height: 3;
    max-height: 8;
    background: {COLORS['bg_secondary']};
    border-top: solid {COLORS['border']};
    padding: 8;
}}

#input-box {{
    border: solid {COLORS['border']};
    background: {COLORS['bg_tertiary']};
    padding-top: 0;
    padding-bottom: 0;
    padding-left: 12;
    padding-right: 12;
}}

#input-box:focus {{
    border: solid {COLORS['border_focus']};
}}

#send-btn {{
    background: {COLORS['accent_purple']};
    color: white;
    padding-top: 0;
    padding-bottom: 0;
    padding-left: 4;
    padding-right: 4;
}}

#send-btn:hover {{
    background: {COLORS['accent_purple_dim']};
}}

#status-bar {{
    height: 1;
    background: {COLORS['bg_secondary']};
    border-top: solid {COLORS['border']};
    color: {COLORS['text_muted']};
}}

.status-item {{
    color: {COLORS['text_muted']};
}}

.status-connected {{
    color: {COLORS['accent_green']};
}}

.status-disconnected {{
    color: {COLORS['accent_red']};
}}

.status-model {{
    color: {COLORS['accent_purple']};
}}

VerticalScroll {{
    scrollbar-color: {COLORS['border']} {COLORS['bg_primary']};
}}

.thinking {{
    color: {COLORS['accent_yellow']};
    text-style: italic;
}}

.separator {{
    color: {COLORS['border']};
}}
"""
