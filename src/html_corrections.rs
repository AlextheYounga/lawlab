use scraper::{ Html, Selector, ElementRef };
use regex::Regex;

fn get_inner_text_formatted(div: ElementRef) -> String {
    let re = Regex::new(r"\s+").unwrap();

    let inner_text = div
        .children()
        .filter_map(|child| ElementRef::wrap(child))
        .flat_map(|el| el.text())
        .collect::<Vec<_>>()
        .join(" ");

    let formatted_text = inner_text.trim().replace("\n", "").replace("\t", " ");
    let replace_spaces = re.replace_all(&formatted_text, " ");
    return replace_spaces.to_string();
}

pub fn handle_html_corrections(contents: &str) -> String {
    let html_contents: Html = Html::parse_document(&contents);
    let mut new_contents = html_contents.clone().html().to_string();
    let analysis_selector: Selector = Selector::parse("div.analysis").unwrap();
    let analysis_divs = html_contents.select(&analysis_selector);

    if analysis_divs.clone().count() == 0 {
        return new_contents;
    }

    for analysis_div in analysis_divs {
        for div in analysis_div.child_elements() {
            let find_value = div.html().to_string();
            let inner_text = get_inner_text_formatted(div);
            let replace_value = format!("<div>{}</div>", &inner_text);
            new_contents = new_contents.replace(&find_value, &replace_value);
        }
    }
    return new_contents;
}
