import 'package:intl/intl.dart';

class UsageHistory {
  final int usageNum;
  final String name;
  final int? robotId;
  final DateTime? startTime;
  final DateTime? stopTime;
  final DateTime? usageDate;

  UsageHistory({
    required this.usageNum,
    required this.name,
    this.robotId,
    this.startTime,
    this.stopTime,
    this.usageDate,
  });

  factory UsageHistory.fromJson(Map<String, dynamic> json) {
    // Flask에서 사용하는 날짜 포맷
    DateFormat startStopFormat = DateFormat("EEE, dd MMM yyyy HH:mm:ss");  // GMT 부분 제거
    DateFormat usageDateFormat = DateFormat("EEE, dd MMM yyyy"); // usage_date 포맷

    // 날짜 파싱 함수
    DateTime? parseDate(String? dateString, DateFormat format) {
      if (dateString == null) return null;
      try {
        // "GMT"를 제거하고 날짜만 파싱
        dateString = dateString.replaceAll(' GMT', '');
        return format.parse(dateString);
      } catch (e) {
        print('Error parsing date: $e');
        return null;
      }
    }

    return UsageHistory(
      usageNum: json['usage_num'],
      name: json['name'],
      robotId: json['robot_id'],
      startTime: parseDate(json['start_time'], startStopFormat),
      stopTime: parseDate(json['stop_time'], startStopFormat),
      usageDate: parseDate(json['usage_date'], usageDateFormat),
    );
  }
}
