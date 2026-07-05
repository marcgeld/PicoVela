import Foundation

/// Minimal CSV table reader for the files emitted by `pico-vela-data`.
public struct CSVTable {
    public let headers: [String]
    public let rows: [[String: String]]

    public init(contentsOf url: URL) throws {
        let text = try String(contentsOf: url, encoding: .utf8)
        self = try CSVTable(text)
    }

    public init(_ text: String) throws {
        let records = CSVTable.parseRecords(text)
        guard let headers = records.first else {
            throw PicoVelaError.emptyCSV
        }

        self.headers = headers
        self.rows = records.dropFirst().map { record in
            Dictionary(uniqueKeysWithValues: headers.enumerated().map { index, header in
                let value = index < record.count ? record[index] : ""
                return (header, value)
            })
        }
    }

    public func require(_ column: String, in row: [String: String]) throws -> String {
        guard let value = row[column] else {
            throw PicoVelaError.missingColumn(column)
        }
        return value
    }

    private static func parseRecords(_ text: String) -> [[String]] {
        var records: [[String]] = []
        var record: [String] = []
        var field = ""
        var insideQuotes = false
        var iterator = text.makeIterator()

        while let character = iterator.next() {
            switch character {
            case "\"":
                if insideQuotes {
                    if let next = iterator.next() {
                        if next == "\"" {
                            field.append("\"")
                        } else {
                            insideQuotes = false
                            if next == "," {
                                record.append(field)
                                field = ""
                            } else if next == "\n" {
                                record.append(field)
                                records.append(record)
                                record = []
                                field = ""
                            } else if next != "\r" {
                                field.append(next)
                            }
                        }
                    } else {
                        insideQuotes = false
                    }
                } else {
                    insideQuotes = true
                }
            case "," where !insideQuotes:
                record.append(field)
                field = ""
            case "\n" where !insideQuotes:
                record.append(field)
                records.append(record)
                record = []
                field = ""
            case "\r" where !insideQuotes:
                continue
            default:
                field.append(character)
            }
        }

        if !field.isEmpty || !record.isEmpty {
            record.append(field)
            records.append(record)
        }

        return records.filter { record in
            record.contains { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
        }
    }
}
