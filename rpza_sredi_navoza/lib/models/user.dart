class User {
  final String id;
  final String email;
  final String name;
  final String? picture;

  User({required this.id, required this.email, required this.name, this.picture});

  factory User.fromJson(Map<String, dynamic> j) => User(
        id: j['id'],
        email: j['email'],
        name: j['name'],
        picture: j['picture'],
      );
}
