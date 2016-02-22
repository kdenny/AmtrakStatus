__author__ = 'kdenny'

from lxml import html, etree

tree = html.fromstring(page.content)

etable = str(tree.xpath('//table'))
print etable
table = etree.XML(etable)
rows = iter(table)
headers = [col.text for col in next(rows)]
for row in rows:
    values = [col.text for col in row]
    print dict(zip(headers,values))

