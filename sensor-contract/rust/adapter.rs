use std::io::{self, Read};

fn valid(line: &str) -> bool {
    let fields: Vec<&str> = line.trim_end_matches(['\\r', '\\n']).split('\\t').collect();
    fields.len() == 6 && fields[0] == "APOLO1" && !fields[1].trim().is_empty()
        && !fields[2].trim().is_empty()
        && (fields[3] == "HOST_OS" || fields[3] == "PHYSICAL_INTERFACE")
        && !fields[4].trim().is_empty()
        && fields[5].parse::<u64>().map(|n| n > 0).unwrap_or(false)
}
fn main() {
    let mut input = String::new();
    if io::stdin().read_to_string(&mut input).is_err() { std::process::exit(2); }
    let ok = valid(input.lines().next().unwrap_or(""));
    println!("{}", if ok { "ACCEPTED" } else { "REJECTED" });
    if !ok { std::process::exit(2); }
}
