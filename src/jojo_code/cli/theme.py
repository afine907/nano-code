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
/* ===========================================================================
   Layout: Claude Code style (explicit container)
   Header (height: 3, fixed)
     └─ Middle (height: 1fr)
          ├─ Sidebar (width: 26, fixed)
          └─ Chat area (width: 1fr)
               ├─ Chat (height: 1fr, scrollable)
               └─ Input (height: 3, fixed at bottom)
   Status bar (height: 1, fixed)
   =========================================================================== */

/* === Global === */
Screen {{
    background: {COLORS["bg_primary"]};
    color: {COLORS["text_primary"]};
}}

/* === Header - fixed at top === */
#header {{
    height: 3;
    background: {COLORS["bg_secondary"]};
    border-bottom: solid {COLORS["border"]};
}}

/* === Middle - fills remaining vertical space === */
#middle {{
    height: 1fr;
    width: 100%;
}}

/* === Sidebar - fixed width, full height === */
#sidebar {{
    width: 26;
    height: 100%;
    background: {COLORS["bg_secondary"]};
    border-right: solid {COLORS["border"]};
}}

.sidebar-section {{
    color: {COLORS["text_muted"]};
    text-style: bold;
    padding-top: 1;
    padding-left: 2;
    padding-bottom: 1;
}}

.sidebar-item {{
    padding-top: 0;
    padding-bottom: 0;
    padding-left: 2;
}}

.sidebar-item:hover {{
    background: {COLORS["bg_hover"]};
}}

.sidebar-item.active {{
    background: {COLORS["accent_purple"]};
    color: white;
}}

/* === Chat area - chat + input stacked === */
#chat-area {{
    width: 1fr;
    height: 100%;
}}

/* === Chat - scrollable main content === */
#chat {{
    width: 100%;
    height: 1fr;
    background: {COLORS["bg_primary"]};
}}

/* === Message bubbles === */
.message-user {{
    background: {COLORS["accent_blue"]};
    color: white;
    padding-top: 6;
    padding-bottom: 6;
    padding-left: 12;
    padding-right: 12;
    margin-top: 4;
    margin-bottom: 4;
    margin-left: 40;
    max-width: 70%;
    width: auto;
}}

.message-assistant {{
    background: {COLORS["bg_tertiary"]};
    border: solid {COLORS["border"]};
    padding-top: 6;
    padding-bottom: 6;
    padding-left: 12;
    padding-right: 12;
    margin-top: 4;
    margin-bottom: 4;
    max-width: 80%;
    width: auto;
}}

.message-tool {{
    background: {COLORS["bg_secondary"]};
    border: solid {COLORS["border"]};
    border-left: solid {COLORS["accent_orange"]};
    padding-top: 4;
    padding-bottom: 4;
    padding-left: 10;
    padding-right: 10;
    margin-top: 4;
    margin-bottom: 4;
    max-width: 80%;
    color: {COLORS["accent_orange"]};
}}

.loading-dots {{
    color: {COLORS["accent_purple"]};
    text-style: bold;
    padding-top: 4;
    padding-bottom: 4;
    padding-left: 12;
}}

#welcome {{
    color: {COLORS["text_muted"]};
    text-style: italic;
    padding-top: 2;
    padding-left: 2;
}}

/* === Input area - fixed at bottom of chat area === */
#input-area {{
    height: 3;
    background: {COLORS["bg_secondary"]};
    border-top: solid {COLORS["border"]};
}}

#prompt {{
    color: {COLORS["accent_purple"]};
    padding-top: 0;
    padding-bottom: 0;
    padding-left: 4;
}}

#input-box {{
    border: solid {COLORS["border"]};
    background: {COLORS["bg_tertiary"]};
    padding-top: 0;
    padding-bottom: 0;
    padding-left: 12;
    padding-right: 12;
}}

#input-box:focus {{
    border: solid {COLORS["border_focus"]};
}}

#send-btn {{
    background: {COLORS["accent_purple"]};
    color: white;
    margin-left: 6;
    padding-top: 0;
    padding-bottom: 0;
    padding-left: 12;
    padding-right: 12;
}}

#send-btn:hover {{
    background: {COLORS["accent_purple_dim"]};
}}

/* === Status bar - fixed at bottom === */
#status-bar {{
    height: 1;
    background: {COLORS["bg_secondary"]};
    border-top: solid {COLORS["border"]};
}}

/* === Header elements === */
#header-title {{
    color: {COLORS["text_primary"]};
    padding-left: 2;
}}

#header-mode {{
    background: {COLORS["accent_purple"]};
    color: white;
    padding-left: 8;
    padding-right: 8;
}}

#header-status {{
    color: {COLORS["text_muted"]};
    padding-left: 8;
}}

#header-spacer {{
    width: 1fr;
}}

#header-conn {{
    padding-right: 2;
}}

/* === Misc === */
.placeholder {{
    color: {COLORS["text_muted"]};
    text-style: italic;
}}

.separator {{
    color: {COLORS["border"]};
}}

.status-connected {{
    color: {COLORS["accent_green"]};
}}

.status-disconnected {{
    color: {COLORS["accent_red"]};
}}

VerticalScroll {{
    scrollbar-color: {COLORS["border"]} {COLORS["bg_primary"]};
}}
"""
