import bpy

# Filter objects so only to return objects of type mesh
def FilterSelection(Objects : list[bpy.types.Object]):
    FilteredObjects = []
    for Object in Objects:
        if(Object.type == "MESH"):
            FilteredObjects.append(Object)

    return FilteredObjects

# Create a variable holding the maximum extension in x,y or z
def CompareBounds(CurrentBounds, CompareBounds):
    for i in range(len(CurrentBounds)):
        if(abs(CompareBounds[i]) > CurrentBounds[i]):
            CurrentBounds[i] = abs(CompareBounds[i])