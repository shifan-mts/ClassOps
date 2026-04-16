import { OAuth2Client } from 'google-auth-library';

const CLASSROOM_BASE_URL = 'https://classroom.googleapis.com/v1';
const MEET_BASE_URL = 'https://meet.googleapis.com/v2';
const MEETING_CODE_PATTERN = /([a-z]{3}-[a-z]{4}-[a-z]{3})/i;

const normalizeMeetingCode = (value) => {
  if (!value) return '';
  const match = String(value).trim().match(MEETING_CODE_PATTERN);
  return match ? match[1].toLowerCase() : '';
};

const buildMeetLink = (meetingCode) => {
  const normalizedCode = normalizeMeetingCode(meetingCode);
  return normalizedCode ? `https://meet.google.com/${normalizedCode}` : null;
};

const parseTimestamp = (value) => {
  if (!value) return null;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};

const formatTimestamp = (value) => {
  const parsed = parseTimestamp(value);
  return parsed ? parsed.toISOString() : null;
};

const getDurationMinutes = (startValue, endValue) => {
  const start = parseTimestamp(startValue);
  if (!start) return 0;
  const end = parseTimestamp(endValue) || new Date();
  return Math.max(0, Math.round(((end.getTime() - start.getTime()) / 60000) * 100) / 100);
};

const googleGet = async (oauthClient, url, searchParams = undefined) => {
  const headers = await oauthClient.getRequestHeaders(url);
  const endpoint = searchParams ? `${url}?${new URLSearchParams(searchParams).toString()}` : url;
  const response = await fetch(endpoint, { headers });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}: ${await response.text()}`);
  }
  return response.json();
};

const listPaged = async (oauthClient, url, itemKey, searchParams = {}) => {
  const items = [];
  let pageToken;

  do {
    const payload = await googleGet(oauthClient, url, {
      ...searchParams,
      ...(pageToken ? { pageToken } : {})
    });
    items.push(...(payload[itemKey] || []));
    pageToken = payload.nextPageToken;
  } while (pageToken);

  return items;
};

const resolveClassroomEmail = async (oauthClient, userId, emailCache) => {
  if (!userId) return null;
  if (emailCache.has(userId)) return emailCache.get(userId);

  const profile = await googleGet(oauthClient, `${CLASSROOM_BASE_URL}/userProfiles/${userId}`);
  const email = profile.emailAddress?.trim().toLowerCase() || null;
  emailCache.set(userId, email);
  return email;
};

export const createGoogleOAuthClient = ({ clientId, clientSecret, redirectUri, credentials }) => {
  const oauthClient = new OAuth2Client(clientId, clientSecret, redirectUri);
  if (credentials) {
    oauthClient.setCredentials(credentials);
  }
  return oauthClient;
};

export const getMeetingLink = async ({ oauthClient, courseId, storedMeetLink = null, storedMeetingCode = null }) => {
  const course = await googleGet(oauthClient, `${CLASSROOM_BASE_URL}/courses/${courseId}`);
  const apiMeetLink = course.meetLink || course.meetingLink || null;
  const meetingCode =
    normalizeMeetingCode(apiMeetLink) ||
    normalizeMeetingCode(storedMeetingCode) ||
    normalizeMeetingCode(storedMeetLink);

  return {
    courseId,
    meetLink: apiMeetLink || storedMeetLink || buildMeetLink(meetingCode),
    meetingCode,
    source: apiMeetLink ? 'classroom_api' : (storedMeetLink || storedMeetingCode ? 'stored_config' : 'unavailable'),
    classroomAlternateLink: course.alternateLink || null
  };
};

export const getAttendanceReport = async ({ oauthClient, meetingCode, studentsByEmail = {} }) => {
  const normalizedCode = normalizeMeetingCode(meetingCode);
  if (!normalizedCode) {
    throw new Error('A valid Google Meet code is required.');
  }

  const conferenceRecords = await listPaged(
    oauthClient,
    `${MEET_BASE_URL}/conferenceRecords`,
    'conferenceRecords',
    {
      filter: `space.meeting_code = "${normalizedCode}"`,
      pageSize: '1'
    }
  );

  if (conferenceRecords.length === 0) {
    return {
      meetingCode: normalizedCode,
      meetingEnded: false,
      attendance: []
    };
  }

  const conferenceRecord = conferenceRecords[0];
  const participants = await listPaged(
    oauthClient,
    `${MEET_BASE_URL}/${conferenceRecord.name}/participants`,
    'participants',
    { pageSize: '100' }
  );

  const emailCache = new Map();
  let meetingEnded = Boolean(conferenceRecord.endTime);
  const attendance = [];

  for (const participant of participants) {
    const leaveTime = participant.latestEndTime || null;
    if (!leaveTime) {
      meetingEnded = false;
    }

    const userId = participant.signedinUser?.user?.split('/').pop();
    const email = await resolveClassroomEmail(oauthClient, userId, emailCache);
    const matchedStudent = email ? studentsByEmail[email] : null;

    attendance.push({
      studentName: matchedStudent?.studentName || matchedStudent?.name || `Participant ${participant.name.split('/').pop()}`,
      email,
      joinTime: formatTimestamp(participant.earliestStartTime),
      leaveTime: formatTimestamp(leaveTime),
      totalDurationMinutes: getDurationMinutes(participant.earliestStartTime, leaveTime)
    });
  }

  return {
    meetingCode: normalizedCode,
    conferenceRecord: conferenceRecord.name,
    meetingEnded,
    attendance
  };
};
