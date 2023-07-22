from urllib.parse import parse_qs
from urllib.parse import urlparse

from markdown_it import MarkdownIt


def render_blank_link(self, tokens, idx, options, env):
    """
    Add target="_blank" to links

    Note: The post editor currently shows a broken image when this is used.
    """
    tokens[idx].attrSet("target", "_blank")
    return self.renderToken(tokens, idx, options, env)


def render_youtube_pin_or_board(self, tokens, idx, options, env):
    """
    Render image syntax with youtube urls as embedded youtube player

    Note: The post editor currently shows a broken image when this is used.
    ex. ![30 for 30 Youtube Skate Part](https://www.youtube.com/watch?v=Lgwlta7ccnI)
    """
    token = tokens[idx]

    if "https://www.youtube.com/watch?v" in token.attrs["src"]:

        results = urlparse(token.attrs["src"])
        if results:
            query_params = parse_qs(results.query)

            ident = query_params["v"][0]

        return (
            '<div class="ratio ratio-16x9">\n'
            f'<iframe width="560" height="315" src="https://www.youtube.com/embed/{ident}"'
            + ' title="YouTube video player"\n'
            + 'frameborder="0" allow="accelerometer; autoplay; clipboard-write;'
            + ' encrypted-media; gyroscope; picture-in-picture"\n allowfullscreen></iframe>\n'
            + "</div>"
        )

    elif "https://www.pinterest.com/pin/" in token.attrs["src"]:

        results = urlparse(token.attrs["src"])
        if results:
            path = results.path

        return (
            '<div class="d-flex justify-content-center">'
            + "<div>"
            + f'<a href="https://www.pinterest.com{path}" data-pin-do="embedPin"></a>'
            + "</div>"
            + "</div>"
        )

    elif "https://www.pinterest.com/" in token.attrs["src"]:

        results = urlparse(token.attrs["src"])
        if results:
            path = results.path

        return (
            '<div class="d-flex justify-content-center">'
            + '<a data-pin-do="embedBoard" data-pin-board-width="400" data-pin-scale-height="240"'
            + f'data-pin-scale-width="80" href="https://www.pinterest.com{path}"></a>'
            + "</div>"
        )

    return self.image(tokens, idx, options, env)


md = MarkdownIt("commonmark").enable("strikethrough")
md.add_render_rule("image", render_youtube_pin_or_board)
md.add_render_rule("link_open", render_blank_link)
