from blog_editor.render import render_body

from conftest import make_png


def render(body, tmp_path, **kw):
    return render_body(body, tmp_path, **kw)


def test_inline_and_display_math_become_mathml(tmp_path):
    r = render("Area $\\pi r^2$.\n\n$$\n\\frac{a}{b}\n$$\n", tmp_path)
    assert '<math xmlns="http://www.w3.org/1998/Math/MathML" display="inline">' in r.html
    assert '<div class="math block">' in r.html and 'display="block"' in r.html
    assert "<mfrac>" in r.html
    assert not r.errors


def test_money_and_escaped_dollars_stay_text(tmp_path):
    r = render("It costs $5 and $10. A literal \\$x\\$ too.", tmp_path)
    assert "<math" not in r.html
    assert "$5 and $10" in r.html and "$x$" in r.html


def test_bad_latex_is_an_error_with_its_line(tmp_path):
    r = render("fine\n\nbroken $\\frac{a}{$ here", tmp_path)
    assert len(r.errors) == 1 and r.errors[0].startswith("line 3:")
    assert 'class="math-error"' in r.html


def test_unknown_latex_command_is_an_error(tmp_path):
    r = render("$\\notacommand{x}$", tmp_path)
    assert r.errors == ["line 1: unknown LaTeX command \\notacommand"]


def test_lone_image_is_a_figure_with_caption_and_size(tmp_path):
    make_png(tmp_path / "shot.png", (1200, 750))
    r = render('![A castle](shot.png "The tide comes in"){.wide}', tmp_path)
    assert r.html.startswith('<figure class="wide"><img src="shot.png" alt="A castle" width="1200" height="750"')
    assert "<figcaption>The tide comes in</figcaption></figure>" in r.html
    assert "<p>" not in r.html


def test_images_in_one_paragraph_are_a_gallery(tmp_path):
    r = render("![a](a.png) ![b](b.png)", tmp_path)
    assert r.html.startswith('<div class="gallery"><figure><img src="a.png"')
    assert r.html.count("<figure>") == 2


def test_inline_image_stays_inline(tmp_path):
    r = render("Look: ![icon](i.png) here.", tmp_path)
    assert "<p>Look: <img" in r.html and "<figure" not in r.html


def test_image_without_alt_warns(tmp_path):
    r = render("![](x.png)", tmp_path)
    assert r.warnings == ["line 1: image x.png has no alt text"]


def test_video_files(tmp_path):
    r = render('![A tide](tide.mp4 "Caption")\n\n![](loop.webm){.loop}', tmp_path)
    assert '<video src="tide.mp4" controls preload="metadata" playsinline aria-label="A tide">' in r.html
    assert '<figure class="loop"><video src="loop.webm" autoplay loop muted playsinline></video></figure>' in r.html


def test_youtube_and_vimeo_embeds(tmp_path):
    r = render("![Trailer](https://youtu.be/dQw4w9WgXcQ?t=90)\n\n![Talk](https://vimeo.com/123456)", tmp_path)
    assert 'src="https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ?start=90" title="Trailer"' in r.html
    assert 'src="https://player.vimeo.com/video/123456?dnt=1"' in r.html


def test_preview_marks_source_lines_and_publish_does_not(tmp_path):
    body = "## Head\n\npara\n\n![x](x.png)\n\n$$\nx\n$$"
    preview = render(body, tmp_path, preview=True).html
    assert '<h2 id="head" data-line="0">' in preview
    assert '<p data-line="2">' in preview
    assert '<figure data-line="4">' in preview
    assert '<div data-line="6" class="math block">' in preview
    assert "data-line" not in render(body, tmp_path).html


def test_footnotes_tables_and_typography(tmp_path):
    r = render('"Quoted" -- yes.[^1]\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n[^1]: A note.', tmp_path)
    assert "“Quoted” – yes." in r.html
    assert "<table>" in r.html and 'class="footnotes"' in r.html
