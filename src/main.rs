mod convert_to_markdown;
mod html_corrections;
use std::fs;
use std::path::PathBuf;
use std::borrow::Cow;
use rayon::prelude::*;
use regex::Regex;
use convert_to_markdown::convert_to_markdown;
use html_corrections::handle_html_corrections;

fn create_document_path(expcite: &str) -> String {
    return String::from(expcite)
        .to_lowercase()
        .trim()
        .replace(" ", "-")
        .replace("expcite:", "")
        .replace(".", "")
        .replace("/", "")
        .replace(",", "")
        .replace("!@!", "/");
}

fn get_expcite(text: &str) -> &str {
    return text.split_once("<!-- expcite:").unwrap().1.split_once("-->").unwrap().0.trim();
}

fn handle_appendix(title_path: PathBuf, contents: String) {
    /* The correct title name is not found in the appendix file itself,
	so I have to find the correct title document by removing the "a" after the title number.
	 */
    let re: Regex = Regex::new(r"\d+a").unwrap();
    let title_doc_name: Cow<'_, str> = title_path.to_string_lossy();
    let title_id = re.find(&title_doc_name).unwrap();
    let title_number = title_id.as_str().replace("a", "");
    let main_title_location = title_doc_name.replace(title_id.as_str(), &title_number);
    let main_title_bytes = fs
        ::read(main_title_location)
        .expect("Should have been able to read the file");
    let main_title_contents = String::from_utf8_lossy(&main_title_bytes);
    let doc_cite = get_expcite(&main_title_contents);
    let filepath = create_document_path(doc_cite) + "/appendix";
    let corrected_contents = handle_html_corrections(&contents);
    return convert_to_markdown(&filepath, corrected_contents);
}

fn main() {
    let titles: Vec<PathBuf> = fs
        ::read_dir("./storage/usc")
        .unwrap()
        .filter_map(|entry| entry.ok().map(|e| e.path()))
        .collect();

    for title_path in titles {
        let title_doc_name: Cow<'_, str> = title_path.to_string_lossy();
        if title_doc_name.ends_with(".htm") {
            let title_bytes: Vec<u8> = fs
                ::read(&title_path)
                .expect("Should have been able to read the file");
            let title_contents: Cow<'_, str> = String::from_utf8_lossy(&title_bytes);
            let title_name = get_expcite(&title_contents);
            println!("{}", title_name);

            if title_name.contains("APPENDIX") {
                handle_appendix(title_path, title_contents.to_string());
                continue;
            }

            let documents = title_contents.split("<!-- documentid");
            documents
                .enumerate()
                .par_bridge()
                .into_par_iter()
                .for_each(|(index, doc)| {
                    // Skip the first
                    if index > 0 {
                        let doc_cite = get_expcite(doc);
                        let mut filepath = create_document_path(doc_cite);
                        let contents = String::from("<!-- documentid") + doc;
                        let corrected_contents = handle_html_corrections(&contents);
                        if doc_cite.contains("!@!Sec.") {
                            // Section document
                            convert_to_markdown(&filepath, corrected_contents);
                        } else {
                            // Front matter
                            filepath += "/frontmatter";
                            convert_to_markdown(&filepath, corrected_contents);
                        }
                    }
                });
        }
    }
}
