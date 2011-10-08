
import re

import lxml.etree


SPACE_PAT = re.compile(r'\s+')

def is_text_lx(el):
    """
    Returns False if an element is a comment or processing instruction
    (<!-- or <?)
    """
    return (el.tag is not lxml.etree.Comment and
        el.tag is not lxml.etree.ProcessingInstruction)

def lx_to_text(el):
    """
    Takes an LXML element.  Returns all containing text, but no comments or JS.
    """
    bits = []
    for child in el.iter():
        if not is_text_lx(child):
            continue # skip comments
        if child.tag == 'script':
            continue # skip script tags
        if child.tag == 'br':
            assert not child.text
            bits.append('\n')
        if child.text:
            bits.append(child.text)
        if child.tail and child is not el:
            # the first item returned by el.iter() is el, but we don't want
            # to include whatever text came after el.iter
            bits.append(child.tail)
    trimmed = trim_spaces(''.join(bits))
    return trimmed.strip()

def lx_and_sel_to_text(lx, sel):
    items = sel(lx)
    if len(items) == 1:
        return lx_to_text(items[0])

def trim_spaces(s):
    """
    Converts one or more spaces in a string to one, throughout the string.
    """
    if isinstance(s, unicode):
        # replace nonbreaking spaces with spaces
        s = s.replace(u'\xa0', u' ')
    return SPACE_PAT.sub(' ', s)
