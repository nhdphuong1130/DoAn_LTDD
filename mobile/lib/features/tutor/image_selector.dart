import 'package:image_picker/image_picker.dart';

class SelectedImage {
  final String name;
  final String path;
  const SelectedImage(this.name, [this.path = '']);
}

abstract interface class ImageSelector {
  Future<SelectedImage?> select();
}

class GalleryImageSelector implements ImageSelector {
  final ImagePicker _picker;
  GalleryImageSelector([ImagePicker? picker])
    : _picker = picker ?? ImagePicker();

  @override
  Future<SelectedImage?> select() async {
    final image = await _picker.pickImage(source: ImageSource.gallery);
    return image == null ? null : SelectedImage(image.name, image.path);
  }
}
