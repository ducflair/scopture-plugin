# Deleting Elements (/docs/guidelines/deleting-elements)



## Delete an Element [#delete-an-element]

To delete an existing element, set its `is_deleted` field to `true`. That flag is sufficient.

Keep the element in the document with its original ID and relationships. Do not remove its record or rely on omission from an update, because omitted elements remain unchanged in patch-based workflows.

`ducpy` and SQL expose the field as `is_deleted`. Other adapters may use their language’s naming convention, such as `isDeleted`, for the same stored property.