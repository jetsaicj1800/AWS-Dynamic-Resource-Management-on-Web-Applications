from PIL import Image
import imghdr


def generate_thumbnail(infile, outfile):
	# generate thumbnail for a given input photo

	size = 128, 128
	im = Image.open(infile)
	im.thumbnail(size)
	im.save(outfile, imghdr.what(infile))

