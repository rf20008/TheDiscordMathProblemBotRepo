import json
import warnings


class DocumentationException(Exception):
    def _raise(self):
        raise self


class DocumentationNotFound(DocumentationException):
    pass


class DocumentationFileNotFound(DocumentationNotFound):
    pass


class DocumentationFileLoader:
    def __init__(self):
        # this is deprecated
        warnings.warn(
            category=DeprecationWarning,
            stacklevel=-1,
            message="The DocumentationFileLoader is being deprecated",
        )

    def _load_documentation_file(self):
        warnings.warn(
            category=DeprecationWarning,
            stacklevel=-1,
            message="The DocumentationFileLoader is being deprecated",
        )
        with open("docs/documentation.json", "r") as file:
            return json.loads("\n".join([str(item) for item in file]))

    def load_documentation_into_readable_files(self):
        warnings.warn(
            category=DeprecationWarning,
            stacklevel=-1,
            message="The DocumentationFileLoader is being deprecated",
        )
        dictToStoreFileContent = {}
        docs_json = self._load_documentation_file()
        for key in docs_json.keys():
            dictToStoreFileContent[
                docs_json["file_name"]  # item is a key, but i forgot what this does
            ] = "<!This file is dynamically generated from documentation.json. If you want to contribute/this is your fork, edit that instead :)>\n"
            if docs_json.get("contains_legend", "false") == "true":
                dictToStoreFileContent[
                    docs_json["file_name"]
                ] += """# Legend - global
        
*: Only useable by users with the Administrator (considering changing it to Manage Server) permission and global trusted users can use.

⚠: Only useable by global trusted users (such as /raise_error)

**: Not a bot/slash command (Documentation is here for purposes of me, and those who wish to fork my project/contribute with pull requests :))

***: This is a module/class. Cannot be called.

No Mark: This is a command without user restrictions"""
            item2 = docs_json["contents"]
            for Item in item2:
                dictToStoreFileContent[docs_json["file_name"]] += (
                    "\n"
                    + "#" * Item.get("heading_level", 0)
                    + " "
                    + Item["title"]
                    + "\n"
                    + Item["contents"]
                )

        for documentationFileName in dictToStoreFileContent.keys():
            with open(documentationFileName, "w") as file:
                file.write(dictToStoreFileContent[documentationFileName])
        return docs_json

    def get_documentation(self, documentationSource, documentationItem):
        _documentation = None
        documentation_from_json = self._load_documentation_file()
        for value in documentation_from_json:
            value_json = value
            if isinstance(value_json, (str, bytes, bytearray)):
                value_json = json.loads(value_json)

            if value_json["file_name"] == documentationSource:
                _documentation = value_json
                break
        if _documentation is None:
            raise DocumentationFileNotFound(
                f"Documentation file {documentationSource} not found"
            )
        if "title" in _documentation.keys():
            if _documentation["title"] != documentationSource:
                raise DocumentationFileNotFound(
                    "Malformed documentation... or it's not found"
                )
            return _documentation
        if _documentation["contents"]["title"] != documentationItem:
            raise DocumentationNotFound("Documentation not found...")
        else:
            return _documentation["contents"]
        raise DocumentationNotFound(f"Documentation for {documentationItem} not found")
