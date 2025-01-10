# Create an iconset directory
mkdir photo_organizer.iconset

# Create PNG files at required sizes
convert photo-organizer-icon.png -resize 16x16 photo_organizer.iconset/icon_16x16.png
convert photo-organizer-icon.png -resize 32x32 photo_organizer.iconset/icon_16x16@2x.png
convert photo-organizer-icon.png -resize 32x32 photo_organizer.iconset/icon_32x32.png
convert photo-organizer-icon.png -resize 64x64 photo_organizer.iconset/icon_32x32@2x.png
convert photo-organizer-icon.png -resize 128x128 photo_organizer.iconset/icon_128x128.png
convert photo-organizer-icon.png -resize 256x256 photo_organizer.iconset/icon_128x128@2x.png
convert photo-organizer-icon.png -resize 256x256 photo_organizer.iconset/icon_256x256.png
convert photo-organizer-icon.png -resize 512x512 photo_organizer.iconset/icon_256x256@2x.png
convert photo-organizer-icon.png -resize 512x512 photo_organizer.iconset/icon_512x512.png
convert photo-organizer-icon.png -resize 1024x1024 photo_organizer.iconset/icon_512x512@2x.png

# Convert the iconset to icns
iconutil -c icns photo_organizer.iconset

# Clean up the iconset directory
rm -rf photo_organizer.iconset
