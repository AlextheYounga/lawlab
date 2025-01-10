use std::fs;
use std::fs::File;
use std::path::PathBuf;
use std::io::{ self, Write };
use std::borrow::Cow;
use html2md::parse_html;
use rayon::prelude::*;
use scraper::{ Html, Selector, ElementRef };
use regex::Regex;

fn write_to_file(filepath: String, buffer: Vec<u8>) -> io::Result<()> {
    let mut file = File::create(filepath)?;
    file.write_all(&buffer)?;
    Ok(())
}

fn create_out_dirs(filepath: &String) -> io::Result<()> {
    fs::create_dir_all(filepath)?;
    Ok(())
}

fn format_citation_comment(citation: &str) -> String {
    return String::from(citation)
        .to_lowercase()
        .trim()
        .replace(" ", "-")
        .replace("expcite:", "")
        .replace(".", "")
        .replace("/", "")
        .replace(",", "")
        .replace("!@!", "/");
}

// fn handle_appendix(doc_path: PathBuf, doc_html: Html) {
//     /* The correct title name is not found in the appendix file itself,
// 	so I have to find the correct title document by removing the "a" after the title number.
// 	 */
//     let re: Regex = Regex::new(r"\d+a").unwrap();
//     let doc_name: Cow<'_, str> = doc_path.to_string_lossy();
//     let title_id = re.find(&doc_name).unwrap();
//     let title_number = title_id.as_str().replace("a", "");
//     let main_doc_location = doc_name.replace(title_id.as_str(), &title_number);
//     let main_doc_bytes = fs
//         ::read(main_doc_location)
//         .expect("Should have been able to read the file");
//     let main_doc_string = String::from_utf8_lossy(&main_doc_bytes);

//     for line in main_doc_string.lines() {
//         if line.contains("expcite") {
//             let citation = format_citation_comment(line);
//             let file_path = citation + "/appendix";
//             // write to file
//         }
//     }
// }

fn find_section_path(section_element: ElementRef<'_>) -> String {
	let mut section_path = String::new();
    for element in section_element.ancestors() {
        if element.value().is_comment() && element.value().as_text().is_some() {
			if element.value().as_text().unwrap().contains("expcite") {
				let item_citation: String = element.value().as_text().unwrap().to_string();
				section_path = format_citation_comment(&item_citation);
				break;
			}
        }
    }
	return section_path;
}

fn find_document_id(section_element: ElementRef<'_>) -> String {
	let mut document_id = String::new();
    for element in section_element.ancestors() {
        if element.value().is_comment() && element.value().as_text().is_some() {
            if element.value().as_text().unwrap().contains("documentid") {
                let item_citation: String = element.value().as_text().unwrap().to_string();
				document_id = item_citation
					.split("documentid:")
					.nth(1)
					.unwrap()
					.split(" ")
					.nth(0)
					.unwrap()
					.trim()
					.to_string();
				break;
            }
        }
    }
	return document_id;
}

fn main() {
    let docs: Vec<PathBuf> = fs
        ::read_dir("./storage/usc")
        .unwrap()
        .filter_map(|entry| entry.ok().map(|e| e.path()))
        .collect();

    for doc_path in docs {
		let doc_name: Cow<'_, str> = doc_path.to_string_lossy();
		if doc_name.ends_with(".htm") {
			let doc_bytes = fs::read(&doc_path).expect("Should have been able to read the file");
			let doc_contents: Cow<'_, str> = String::from_utf8_lossy(&doc_bytes);
			let doc_html: Html = Html::parse_document(&doc_contents);
			let title_head_selector: Selector = Selector::parse("h1.usc-title-head").unwrap();
			let title_element: ElementRef<'_> = doc_html.select(&title_head_selector).next().unwrap();
			let title: String = String::from(title_element.inner_html().as_str());
			println!("{}", title);
	
			if title.contains("APPENDIX") {
				continue;
				// return handle_appendix(doc_path, doc_html);
			}
	
			let section_selector = Selector::parse("h3.section-head").unwrap();
			let mut section_elements = doc_html.select(&section_selector);
			let mut sections = doc_contents.split("<h3 class=\"section-head\">");
			// Pop the first value
			let mut front_matter = "";
			if let Some(first_value) = sections.next() {
				front_matter = first_value;
			}
	
			// Map out all the html we'll need before converting.
			let mut section_vec: Vec<[String; 3]> = Vec::new();
			let sections_count = sections.clone().count();
			for (i, section) in sections.into_iter().enumerate() {
				let section_element = section_elements.next().unwrap();
				let mut section_content = section_element.html() + section;
				if i == 0 {
					section_content.insert_str(0, front_matter); // that's dumb...
				}
				if i == sections_count - 1 {
					section_content.insert_str(0, "<html><body><div>");
				}
	
				// Get item "citation" from document which contains the path.
				let section_path = find_section_path(section_element);
				let document_id = find_document_id(section_element);
	
				section_vec.push([document_id, section_path, section_content])
			}
	
			// Run in parallel to convert to markdown
			section_vec.par_iter().for_each(|doc_items| {
				let doc_id = &doc_items[0];
				let section_path = &doc_items[1];
				let section_content = &doc_items[2];

				// Convert to markdown
            	let markdown = parse_html(&section_content);
            	let buffer = markdown.into_bytes();
				let out_path = String::from("out/usc/") + section_path + ".md";

				if create_out_dirs(&out_path).is_ok() {
					// println!("Would output {}", &out_path);
					// if let Err(e) = write_to_file(mdfilename, buffer) {
					// 	eprintln!("Error writing to file: {}", e);
					// }
				}

			})
		}
    }
}