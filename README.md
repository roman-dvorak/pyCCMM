# pyCCMM - Python CCMM Metadata Handler

Python parser and metadata generator for [Czech Core Metadata Model (CCMM)](https://techlib.github.io/CCMM/en/).

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic usage

```python
from pyccmm import CCMMHandler

# Initialize handler (uses bundled CCMM schemas)
handler = CCMMHandler()

# Set basic required fields
handler.set_title("My dataset")
handler.set_publication_year(2024)

# Add identifier
handler.add_identifier("12345", "DOI")

# Add description
handler.add_description("Dataset description")

# Validation
if handler.is_valid():
    print("Dataset is valid!")
    
# Save to file
handler.save_to_file("metadata.xml")
```

### Gradual parameter filling

```python
# Add metadata as needed
handler.add_subject("keyword", "CCMM")
handler.add_agent_relationship("Author", "creator", "person")
handler.add_distribution("https://example.com/data", "text/csv")
handler.add_location("Prague", "place")
handler.add_time_reference("2024-01-01", "created")
```

### Loading from file

```python
# Load existing metadata file
handler = CCMMHandler()
if handler.load_from_file("existing_metadata.xml"):
    print("File loaded successfully!")
    print("Title:", handler.get_title())
```

## API Reference

### CCMMHandler

Main class for CCMM metadata manipulation.

#### Constructor
- `__init__(ccmm_path: Optional[str] = None)` - Initializes handler with path to CCMM schemas (uses bundled schemas if None)

#### Required fields
- `set_title(title: str)` - Set dataset title
- `set_publication_year(year: int)` - Set publication year
- `add_identifier(value: str, scheme: IdentifierScheme, iri: Optional[str] = None)` - Add identifier

#### Optional fields
- `set_version(version: str)` - Set version
- `add_description(text: str)` - Add description
- `add_alternate_title(title: str, title_type: Optional[str] = None)` - Add alternate title
- `add_subject(subject: str, scheme: Optional[str] = None)` - Add subject/keyword
- `add_agent_relationship(agent_name: str, role: AgentRole, agent_type: AgentType = AgentType.PERSON)` - Add agent relationship
- `add_distribution(access_url: str, format_type: Optional[DistributionFormat] = None)` - Add distribution
- `add_location(location: str, location_type: LocationType)` - Add location
- `add_time_reference(time_value: str, time_type: TimeReferenceType)` - Add time reference

#### Validation
- `is_valid() -> bool` - Check overall validity (includes XSD validation)

#### Import/Export
- `load_from_file(xml_file_path: str) -> bool` - Load from file
- `save_to_file(file_path: str)` - Save to file
- `to_xml_string(pretty_print: bool = True) -> str` - Convert to XML string

#### Querying
- `get_title() -> str` - Get dataset title
- `get_publication_year() -> int` - Get publication year
- `get_identifiers() -> List[Identifier]` - Get all identifiers
- `get_subjects() -> List[Subject]` - Get all subjects
- `get_summary() -> Dict[str, Any]` - Get dataset summary

## CCMM Structure

The library supports the following CCMM structure:

- **Dataset** (root element)
  - title (required)
  - publication_year (required)
  - identifier (required)
  - version
  - description
  - alternate_title
  - subject
  - qualified_relation (agent relationships)
  - distribution
  - location
  - time_reference
  - and more...

## CCMM Schema Integration

This library includes the official CCMM schemas as a git submodule from the [CCMM repository](https://github.com/techlib/CCMM). The schemas are automatically bundled with the package and used for validation.

## Examples

See `examples/example_usage.py` for complete usage examples.

## Dependencies

- `lxml` - for XSD validation
- `xml.etree.ElementTree` - for XML manipulation (part of Python standard library)
- `typing` - for type hints (part of Python standard library)

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome.

---

*Developed by Roman Dvořák (<romandvorak@mlab.cz>) at the Institute of Physics of the Czech Academy of Sciences (FZU).*
