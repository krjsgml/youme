import 'package:flutter/material.dart';
import 'package:youme_app/models/team_member.dart';

class MemberList extends StatelessWidget {
  final List<TeamMember> members;

  MemberList({required this.members});

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: members.length,
      itemBuilder: (context, index) {
        final member = members[index];
        return ListTile(
          title: Text(member.name),
          subtitle: Text("Phone: ${member.phoneNumber}\nPosition: ${member.position}"),
        );
      },
    );
  }
}
