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
                docs_json["file_name"] # item is a key, but i forgot what this does
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
        for key, value in documentation_from_json.items():
            print(key, value)
            if value["file_name"] == documentationSource:
                _documentation = value
                break
        if _documentation is None:
            raise DocumentationFileNotFound(
                f"Documentation file {documentationSource} not found"
            )

        for item2 in _documentation["contents"]: # try to find the documentation by looping
            if item2["title"] == documentationItem:
                return item2["contents"]
        raise DocumentationNotFound(f"Documentation for {documentationItem} not found")
