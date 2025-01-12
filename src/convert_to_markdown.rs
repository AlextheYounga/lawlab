use std::fs;
use std::fs::File;
use std::path::Path;
use std::io::{ self, Write };
use html2md::parse_html;

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

pub fn convert_to_markdown(filepath: &str, contents: String) {
    let markdown = parse_html(&contents);
    let buffer = markdown.into_bytes();
    let out_path = String::from("out/usc/") + filepath + ".md";

    if create_out_dirs(&out_path).is_ok() {
        if let Err(e) = write_to_file(out_path, buffer) {
            eprintln!("Error writing to file: {}", e);
        }
    }
}