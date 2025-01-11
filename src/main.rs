use std::fs;
use std::fs::File;
use std::path::{ Path, PathBuf };
use std::io::{ self, Write };
use std::borrow::Cow;
use html2md::parse_html;
use rayon::prelude::*;
use regex::Regex;

fn write_to_file(filepath: String, buffer: Vec<u8>) -> io::Result<()> {
    let mut file = File::create(filepath)?;
    file.write_all(&buffer)?;
    Ok(())
}

fn create_out_dirs(filepath: &String) -> io::Result<()> {
    let path = Path::new(filepath);
    let dir_path = path.parent().unwrap();
    fs::create_dir_all(dir_path)?;
    Ok(())
}

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

fn convert_to_markdown(filepath: &str, contents: String) {
    let markdown = parse_html(&contents);
    let buffer = markdown.into_bytes();
    let out_path = String::from("out/usc/") + filepath + ".md";

    if create_out_dirs(&out_path).is_ok() {
        if let Err(e) = write_to_file(out_path, buffer) {
            eprintln!("Error writing to file: {}", e);
        }
    }
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
    return convert_to_markdown(&filepath, contents);
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
                    if index > 0 {
                        // Skip the first
                        let doc_cite = get_expcite(doc);
                        let mut filepath = create_document_path(doc_cite);
                        if doc_cite.contains("!@!Sec.") {
                            // Section document
                            let contents = String::from("<!-- documentid") + doc;
                            convert_to_markdown(&filepath, contents);
                        } else {
                            // Front matter
                            let contents = String::from("<!-- documentid") + doc;
                            filepath += "/frontmatter";
                            convert_to_markdown(&filepath, contents);
                        }
                    }
                });
        }
    }
}
