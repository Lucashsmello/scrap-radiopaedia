from typing import Any


def extract_header(node) -> dict[str, Any]:
    data = {}

    assert len(node.xpath('.//div[@class="col-sm-3"]/text()').getall()) == 0
    header_row_names = node.xpath('.//div[@class="col-sm-3"]/strong/text()').getall()
    header_row_values = [x.xpath('.//text()[normalize-space()]').getall()
                         for x in node.xpath('.//div[@class="col-sm-8"]')]

    header_row_names = [s.strip().rstrip(':').rstrip() for s in header_row_names]

    ### Tags: ###
    # Remove tags from extracted rows.
    # Tags are more reliable extracted with another xpath expression
    if 'Tags' in header_row_names:
        tags_index = header_row_names.index('Tags')
        del header_row_names[tags_index]
        del header_row_values[tags_index]

        header_tags_node = node.xpath('.//a[starts-with(@href,"/tags/")]')
        header_tags_hrefs_values = header_tags_node.xpath('@href').re(r'/tags/([^\?]*)')
        header_tags_texts_values = header_tags_node.xpath('text()').getall()
        assert all(v1 == v2.replace(' ', '-')
                   for v1, v2 in zip(header_tags_hrefs_values, header_tags_texts_values)), f"{header_tags_hrefs_values}!={header_tags_texts_values}"
        data['Tags'] = header_tags_texts_values
    #################

    ### Systems: ###
    # Remove systems from extracted rows.
    # System names are more reliable extracted with another xpath expression
    if 'Systems' in header_row_names:
        system_index = header_row_names.index('Systems')
        del header_row_names[system_index]
        del header_row_values[system_index]
        header_system_node = node.xpath('.//a[starts-with(@href,"/articles/section/")]')
        header_system_texts_values = header_system_node.xpath('text()').getall()
        data['Systems'] = header_system_texts_values
    #################

    data.update({name.replace(' ', '_'): val for name, val in zip(header_row_names, header_row_values)})

    return data
