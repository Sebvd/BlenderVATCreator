# Downloading the Blender plugin
Download the ZIP from this GitHub directory.
In Blender, go to *edit > Preferences > Add-ons > Install from disk*

<img width="660" height="436" alt="afbeelding" src="https://github.com/user-attachments/assets/0544b320-d25b-4e09-b62d-57f12a67e863" />

The plugin should now be good to go.

# Downloading the Unreal Engine plugin
Download the Plugin folder from [its GitHub](https://github.com/Sebvd/UnrealVATTools) and extract it. Create a new folder in your Unreal project folder called "Plugins", and paste the folder there.

# Exporting VATs
## Creating the files with the Blender plugin
<img width="407" height="170" alt="afbeelding" src="https://github.com/user-attachments/assets/031e5330-d761-4906-aec7-648c6dbd5099" />

### Main settings
By opening up the vat tools tab, you will find the main window for the VAT tools. To properly configure your VAT, you have a list of settings to your disposal:
- Frame Start: The starting frame of your simulation.
- Frame End: The ending frame of your simulation
- Frame Spacing: How much "space" in between each frame. For example, imagine a frame range between 1 and 10. If frame spacing is set to 1, this range would be "1,2,3,..10". But if set to 3, this would be "1,4,7,10". This allows you to reduce the FPS in your scene.
- VAT type: The type of vertex animation:
- + SoftBody: For softbody simulations such as cloth.
  + RigidBody: For rigidbody simulations such as destruction.
  + Fluid: For dynamic simulations such as fluids.

### Texture & JSON settings
These settings help you convert between different coordinate spaces for your target engine.

<img width="412" height="176" alt="afbeelding" src="https://github.com/user-attachments/assets/59171b9e-7761-4932-ab67-a2d5e6ef37bb" />

You can click the Icon in the top right corner to automatically select a preset for some of the main game engines.
- Target coords: Target coordinate system axis order.
- Flip coords: Whether or not to negate the x, y or z components.
- Max U: Maximum size of the target position texture.
- Max U (Data): Only applicable to fluid simulations. Maximum size of the target data texture.

### Mesh settings
These settings are applicable to the VAT mesh and how it behaves over the duration of the VAT simulation.

<img width="411" height="286" alt="afbeelding" src="https://github.com/user-attachments/assets/d62fb4a4-0f8c-433f-b967-243fac8305ce" />

- Rest pose: The pose of the simulation without any of the animations applied.
- Split at hard edges: Because VATs are determined per-vertex, the normals of the mesh are stored per-vertex as well, causing vertex normals that are always smooth. If you tick this box, the vertices are split so we can get hard edges, at the cost of a little bit of extra performance and texture size.
- LODs: How many extra LOD meshes to generate. These are stored as separate files. Use the "reduction rate" parameter to determine how strong the polygons should be reduced.

### Export settings
Settings on how to export and store your VAT files. Note that this might look a bit different for every VAT type. Every individual export section has a checkbox. Unchecking it will prevent the plugin from exporting them.

<img width="406" height="328" alt="afbeelding" src="https://github.com/user-attachments/assets/b26361b2-07f8-45af-8dee-1d31578cedd3" />

- Output directory: Which directory to store your files in.
- VAT mesh: The target name of the VAT mesh. Uncheck the checkbox if you do not wish to export this.
- Simulation DATA JSON file: The target name of the VAT JSON file. This file contains necessary data that allows us to properly set up our VAT simulation inside of our target engine.
- VAT textures: These are different depending on the VAT type you have selected on the top. For each texture, you can create a file name and a file format.
- The scale texture (for rigidbody simulations) has one extra feature: Whether or not to pack uniform scale in the position texture. This is an optimized way to transfer scale into your VAT simulation, but it only works for uniform scales.

### Exporting
Once you have adjusted all the settings to your liking, you can hit the "export" button. There are some important "catches" you need to be aware of:
- Please keep the polycount of your meshes in mind. High polycounts not only take really long to compute, but could also result in unusable VAT files. For example, high polycounts can create really big VAT textures, which will most definitely cause precision errors in the shader. For that reason, please have a moderate polycount (e.g., you are already getting high around the 30K-50K mark). (This does not apply to rigidbody simulations - for that its main bottleneck is the number of individual objects).
- Depending on the complexity of the simulation and the number of frames, computation might take quite long. This goes especially for fluid simulations.

# Assembling the VAT simulation in Unreal Engine

## Preparing the VAT mesh
For importing the VAT mesh, you can use the default settings. However, if you use multiple meshes, make sure "combine meshes" is enabled.

<img width="1004" height="991" alt="afbeelding" src="https://github.com/user-attachments/assets/43a5e1f0-ae64-400d-aca8-046b16ad11d3" />

After that, RMB on your mesh and navigate to: *Scripted asset actions > Process VAT mesh*

<img width="737" height="634" alt="afbeelding" src="https://github.com/user-attachments/assets/3f926657-f074-46e5-bf0b-486eebba06e6" />

This will create a popup. In here, select the three dots to open your file explorer. In your file explorer, navigate to the JSON file that was generated by the python script. Afterwards, hit "OK"

<img width="432" height="259" alt="afbeelding" src="https://github.com/user-attachments/assets/a0d2f14a-d938-4bf5-aea0-333af5e66870" />

## Preparing the VAT textures
Next up, you can import your VAT textures. After you have imported them, make sure to process these as well. You can do this by RMB on the texture, and then navigating to: *Scripted asset actions > Process 8/16 bit VAT*. The main difference between 8bit and 16bit VAT is the precision. 16bit is more precise, but will have a bigger impact on memory load.
I recommend using this as follows (please note that this is a guideline - in the end it depends on the use case):
- Position texture: 16bit
- Normal/rotation texture: 8bit
- Scale texture (for rigidbody simulations): 8bit
- Data texture (for dynamic simulations): 16bit

<img width="659" height="700" alt="afbeelding" src="https://github.com/user-attachments/assets/ef38a5ad-8225-4fe6-889b-744e4cb9d684" />

## Preparing the VAT materials
Next up, you will want to make your VAT material. This works a bit differently from every VAT type:

### Softbody VAT materials
- + Create an empty material.
  + Navigate to: *Plugins > VATTools content > MaterialFunctions > MF_VATSoftBodyDeformer* and add it to your material.
  + Select your result / "main" material node, and navigate to "num customized UVs". Set this value from 0 to 5.
  + Hook up the nodes as displayed below.

<img width="512" height="755" alt="afbeelding" src="https://github.com/user-attachments/assets/cb378b4c-65b1-49f5-b326-518fc81d2b81" />

- Save your material and go back to the content browser.
- Right click your material and create a new material instance.
- Right click your material instance, and navigate to: *Scripted asset actions > Process VAT softbody material instance"
- This will open a tab as seen below.

<img width="711" height="351" alt="afbeelding" src="https://github.com/user-attachments/assets/a07fa0ce-251f-4e5b-839f-6bac82c27294" />

- In this tab, select the JSON file similarly as we did before with the VAT mesh.
- Give it the position and normal texture we imported.
- Hit OK
- Applying the new material instance to your VAT mesh will result in a working simulation.

<img width="624" height="478" alt="afbeelding" src="https://github.com/user-attachments/assets/3a6c185d-e952-4a40-904e-c61cf910fa6c" />

ADVANCED: It is also possible to manually adjust the parameters directly in the shader or the material instance:

<img width="316" height="435" alt="afbeelding" src="https://github.com/user-attachments/assets/45ae80b2-1f06-45ba-a221-e8f7b67481f9" />

- FrameCount: The amount of frames in the simulation. This data is stored by default in the JSON file.
- FPS: Frames per second. In most cases, it is 24 by default (as that is the Blender default).
- Time: The current time. Is Unreal time by default.
- UV: The UV channel containing the VAT UVs. By default, it is UV1.
- Looping: Whether or not the animation is a looping animation. This is mostly relevant for interpolation: If interpolation is enabled, it smooths between frames. If you have looping enabled, it interpolates the first and last frames.
- Position texture: The texture containing the position data.
- Bounds: The maximum distance the vertices travel in. This data is stored in the JSON file generated by the python plugin.
- Interpolate position: Whether or not to interpolate between pixels in the shader. Enabling this creates a smoother playback, but it also has an effect on performance, as it increases the number of texture samples.
- Normal texture: The texture containing the vertex normal data.
- Interpolate normals: Whether or not to interpolate between pixels in the shader. Enabling this creates a smoother playback, but it also has an effect on performance, as it increases the number of texture samples.

### Rigidbody VAT materials
- + Create an empty material.
  + Navigate to: *Plugins > VATTools content > MaterialFunctions > MF_VATRigidBodyDeformer* and add it to your material.
  + Select your result / "main" material node, and navigate to "num customized UVs". Set this value from 0 to 6.
  + Hook up the nodes as displayed below.

<img width="605" height="509" alt="afbeelding" src="https://github.com/user-attachments/assets/eee64e97-4a0f-470b-a061-1697ad4f98b4" />

- Save your material and go back to the content browser.
- Right click your material and create a new material instance.
- Right click your material instance, and navigate to: *Scripted asset actions > Process VAT rigidbody material instance"
- This will open a tab as seen below.

<img width="421" height="336" alt="afbeelding" src="https://github.com/user-attachments/assets/a2f55b8c-fa76-48c4-bfcd-263e57c1b0cd" />

- In this tab, select the JSON file that the Blender script generated.
- Additionally, give it the textures you have imported (if you do not have a scale texture, you are not obligated to select it here).
- Hit OK
- Applying the new material instance to your VAT mesh will result in a working simulation.

<img width="711" height="412" alt="afbeelding" src="https://github.com/user-attachments/assets/189e0c64-c7da-46d3-ab03-ad8535ac005d" />

ADVANCED: It is also possible to manually adjust the parameters directly in the shader or the material instance:

<img width="240" height="474" alt="afbeelding" src="https://github.com/user-attachments/assets/89e0eb18-2e09-4c14-85a4-83a4686098a1" />

- Frame Rate: Frame rate in FPS.
- Time: Current time in seconds. By default is set to Unreal time with the time node.
- Frame Count: Number of frames in the simulation. This data is stored in the JSON file as well.
- UV: The UVs that store data necessary for the vertex animation. By default, these are the UVs stored in UV1.
- Whether or not the animation is a looping animation. This is mostly relevant for interpolation: If interpolation is enabled, it smooths between frames. If you have looping enabled, it interpolates the first and last frames.
- Position texture: The texture storing the object position data.
- Position bounds: How much the objects have moved in the VAT simulation. This data is stored in the JSON file as well.
- Interpolate position: Whether or not to interpolate between pixels in the shader. Enabling this creates a smoother playback, but it also has an effect on performance, as it increases the number of texture samples.
- Rotation texture: Texture that stores the rotation of the object in the simulation.
- Interpolate rotation: Whether or not to interpolate between pixels in the shader. Enabling this creates a smoother playback, but it also has an effect on performance, as it increases the number of texture samples.
- Scale enabled: Whether or not scale is enabled for this simulation.
- Scale texture: Texture containing the mesh scale.
- Scale Bounds: How much the objects were scaled during the simulation. This data is stored in the JSON file as well.
- Interpolate scale: Whether or not to interpolate between pixels in the shader. Enabling this creates a smoother playback, but it also has an effect on performance, as it increases the number of texture samples.
- Scale in Alpha: Wether or not (uniform) scale is packed into the alpha channel of the position texture.

### Dynamic VAT materials
- + Create an empty material.
  + Navigate to: *Plugins > VATTools content > MaterialFunctions > MF_VATDynamic* and add it to your material.
  + Select your result / "main" material node, and navigate to "num customized UVs". Set this value from 0 to 4.
  + Hook up the nodes as displayed below.
 
<img width="697" height="455" alt="afbeelding" src="https://github.com/user-attachments/assets/c74f22ad-a2cb-4472-98fe-bd20292ce056" />

- Save your material and go back to the content browser.
- Right click your material and create a new material instance.
- Right click your material instance, and navigate to: *Scripted asset actions > Process VAT rigidbody material instance"
- This will open a tab as seen below.

<img width="416" height="327" alt="afbeelding" src="https://github.com/user-attachments/assets/6849ce3b-2a72-4082-bda7-2a7c1d5f7f23" />

- In this tab, select the JSON file similarly as we did before with the VAT mesh.
- Give it the position, normal and data texture we imported.
- Hit OK
- Applying the new material instance to your VAT mesh will result in a working simulation.

<img width="642" height="587" alt="afbeelding" src="https://github.com/user-attachments/assets/38bd0b18-032b-455c-b503-4f1b1605fb7e" />

ADVANCED: It is also possible to manually adjust the parameters directly in the shader or the material instance:

<img width="301" height="431" alt="afbeelding" src="https://github.com/user-attachments/assets/5f42d245-c116-4e89-a26b-0e318b906b51" />

- Frame Rate: Frame rate in frames per second.
- Time: The current time in seconds. By default, it is Unreal time as set with the time node.
- UV: The UVs storing the VAT data. By default it is UV0 and it should not be changed (behind the scenes, Blender removes all UV channels on the VAT mesh, as they do not get preserved anyways. Instead, it transfers the UVs through the data texture. If you had any mesh UVs, you can retrieve it through the "Mesh UVs" output).
- Frame Count: The number of frames in the simulation. This data is stored in the JSON file as well.
- Position texture: The texture storing the vertex position data.
- Position bounds min: The local bounds minimum of the dynamic simulation. This data is stored in the JSON file.
- Position bounds max: The local bounds max of the dynamic simulation. This data is stored in the JSON file.
- Normal texture: The texture storing the vertex normal data.
- Data texture: The texture storing data for the dynamic simulation. This texture is necessary and essential to make the dynamic VAT work.

# Optimizing the VAT simulation
There are a number of method to optimize the VAT simulation:
- Lowering the polycount: Lowering the polycounts not only reduces texture sizes, but also the load on the vertex shader.
- Lowering the polycount by not preserving hard edges (softbody & dynamic).
- Not interpolating on a shader level: Interpolation uses extra texture samples. Instead, you can also do interpolation using the texture filter. By default, the tool sets the filtering method to "nearest". Instead, you can also use bi-linear, which smooths pixels automatically for you. Please note though that this works best on low polycounts / small textures. 

<img width="599" height="234" alt="afbeelding" src="https://github.com/user-attachments/assets/b8098520-3ab4-47cf-9087-ff9e6fbffcd1" />

- Using rigidbody sim wherever possible: Rigid body simulations do not have limitations on polycounts, and are therefore much more performant. If there are some parts of your simulation that do not deform, consider using rigidbody for those instead.

# Example content
If you navigate to: *Plugins > VATTools content > Samples > L_SampleVATs* you will be able to find several examples in a level that can be used as reference.

<img width="1205" height="680" alt="afbeelding" src="https://github.com/user-attachments/assets/71c57a6f-221c-43d6-8eb4-a7c54f29ff73" />


