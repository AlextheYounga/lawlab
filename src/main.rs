use std::fs;
use std::fs::File;
use std::io::{self, Write};
use html2md::parse_html;
use rayon::prelude::*;
use std::path::PathBuf;


fn write_to_file(filepath: String, buffer: Vec<u8>) -> io::Result<()> {
    let mut file = File::create(filepath)?;
    file.write_all(&buffer)?;
    Ok(())
}

fn create_markdown_dir() -> io::Result<()> {
	fs::create_dir_all("./out/templates/markdown")?;
    Ok(())
}

fn main() {
    // Collect paths into a Vec<PathBuf>
    let paths: Vec<PathBuf> = fs::read_dir("./out/templates/html")
        .unwrap()
        .filter_map(|entry| entry.ok().map(|e| e.path()))
        .collect();
	
	if create_markdown_dir().is_ok() {
		paths.par_iter().for_each(|filepath| {
			let contents = fs::read_to_string(filepath).expect("Should have been able to read the file");
			let markdown = parse_html(&contents);
			let buffer = markdown.into_bytes();
			let mdfilename = filepath
				.to_string_lossy()
				.replace("/html/", "/markdown/")
				.replace(".html", ".md");
	
			if let Err(e) = write_to_file(mdfilename, buffer) {
				eprintln!("Error writing to file: {}", e);
			}
		});
    }
}
