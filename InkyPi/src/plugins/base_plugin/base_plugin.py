import logging
import os
import re
from utils.app_utils import resolve_path, get_fonts
from utils.image_utils import take_screenshot_html
from utils.image_loader import AdaptiveImageLoader
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
import asyncio
import base64

logger = logging.getLogger(__name__)

STATIC_DIR = resolve_path("static")
PLUGINS_DIR = resolve_path("plugins")
BASE_PLUGIN_DIR =  os.path.join(PLUGINS_DIR, "base_plugin")
BASE_PLUGIN_RENDER_DIR = os.path.join(BASE_PLUGIN_DIR, "render")

FRAME_STYLES = [
    {
        "name": "None",
        "icon": "frames/blank.png"
    },
    {
        "name": "Corner",
        "icon": "frames/corner.png"
    },
    {
        "name": "Top and Bottom",
        "icon": "frames/top_and_bottom.png"
    },
    {
        "name": "Rectangle",
        "icon": "frames/rectangle.png"
    }
]

class BasePlugin:
    """Base class for all plugins."""
    def __init__(self, config, **dependencies):
        self.config = config

        # Initialize adaptive image loader for device-aware image processing
        self.image_loader = AdaptiveImageLoader()

        self.render_dir = self.get_plugin_dir("render")
        if os.path.exists(self.render_dir):
            # instantiate jinja2 env with base plugin and current plugin render directories
            loader = FileSystemLoader([self.render_dir, BASE_PLUGIN_RENDER_DIR])
            self.env = Environment(
                loader=loader,
                autoescape=select_autoescape(['html', 'xml'])
            )

    def generate_image(self, settings, device_config):
        raise NotImplementedError("generate_image must be implemented by subclasses")

    def cleanup(self, settings):
        """Optional cleanup method that plugins can override to delete associated resources.

        Called when a plugin instance is deleted. Plugins should override this to clean up
        any files, external resources, or other data associated with the plugin instance.

        Args:
            settings: The plugin instance's settings dict, which may contain file paths or other resources
        """
        pass  # Default implementation does nothing

    def get_plugin_id(self):
        return self.config.get("id")

    def get_plugin_dir(self, path=None):
        plugin_dir = os.path.join(PLUGINS_DIR, self.get_plugin_id())
        if path:
            plugin_dir = os.path.join(plugin_dir, path)
        return plugin_dir

    def generate_settings_template(self):
        template_params = {"settings_template": "base_plugin/settings.html"}

        settings_path = self.get_plugin_dir("settings.html")
        if Path(settings_path).is_file():
            template_params["settings_template"] = f"{self.get_plugin_id()}/settings.html"

        template_params['frame_styles'] = FRAME_STYLES
        return template_params

    def render_image(self, dimensions, html_file, css_file=None, template_params={}):
        # load the base plugin and current plugin css files
        css_files = [os.path.join(BASE_PLUGIN_RENDER_DIR, "plugin.css")]
        if css_file:
            plugin_css = os.path.join(self.render_dir, css_file)
            css_files.append(plugin_css)

        # inline CSS content so the HTML is self-contained for backend rendering
        inline_styles = []
        for css_path in css_files:
            if os.path.exists(css_path):
                with open(css_path, 'r') as f:
                    inline_styles.append(f.read())

        template_params["inline_styles"] = inline_styles
        template_params["width"] = dimensions[0]
        template_params["height"] = dimensions[1]

        # inline fonts as base64 data URLs so they resolve on the backend
        font_faces = get_fonts()
        for font in font_faces:
            font_path = font["url"]
            if os.path.exists(font_path):
                with open(font_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                    font["url"] = f"data:font/ttf;base64,{b64}"
            else:
                logger.warning(f"Font file not found: {font_path}")
        template_params["font_faces"] = font_faces
        template_params["static_dir"] = STATIC_DIR

        # load and render the given html template
        template = self.env.get_template(html_file)
        rendered_html = template.render(template_params)

        # inline any <script src="..."> tags so scripts resolve on the backend
        def _inline_script(match):
            src = match.group(2)
            filepath = src if os.path.isabs(src) else os.path.join(STATIC_DIR, src)
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return f"<script>\n{f.read()}\n</script>"
            logger.warning(f"Script file not found for inlining: {filepath}")
            return match.group(0)

        rendered_html = re.sub(
            r'<script\s+([^>]*?)src=["\']([^"\']+)["\'][^>]*>\s*</script>',
            _inline_script,
            rendered_html
        )

        return take_screenshot_html(rendered_html, dimensions)
