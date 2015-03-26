var oksched = oksched || {}
oksched.selectedTeacherId = function() {
  return $("#teacher").val()
}
oksched.selectedStudentId = function() {
  return $("#student").val()
}
oksched.reload = function() {
  $('.calendar').fullCalendar('refetchEvents')
}

$(document).ready(function() {
  if ($('#student').length) $('#student').change(oksched.reload)
  $('#teacher').change(oksched.reload)

  $('#teacher-calendar').fullCalendar({
    events: {
      url: '/teacher_events',
      data: function() {
        return { teacher_id: oksched.selectedTeacherId() }
      }
    },
    defaultView: 'agendaWeek',
    allDaySlot: false,
    defaultTimedEventDuration: "00:30:00",
    selectable: true,
    select: function(start, end) {
      $.post("/add", {
               start_time: start.unix(),
               end_time:   end.unix(),
               teacher_id: oksched.selectedTeacherId()
             }, oksched.reload)
    },
    editable: false,
    eventClick: function(event) {
      if (window.confirm("Do you really want to remove this availability?")) {
        $.ajax({
          url: "/remove",
          type: "DELETE",
          data: { teacher_id: oksched.selectedTeacherId(), start_time: event.start.unix() },
          success: oksched.reload
        })
      }
    }
  })

  $('#student-calendar').fullCalendar({
    events: {
      url: '/events',
      data: function() { return { student_id: oksched.selectedStudentId(), teacher_id: oksched.selectedTeacherId() } }
    },
    defaultView: 'agendaWeek',
    allDaySlot: false,
    defaultTimedEventDuration: "00:30:00",
    selectable: false,
    editable: false,
    eventClick: function(event) {
      if (event.color == 'green' || event.color == 'red') {
        if (window.confirm("Do you really want to cancel this session?")) {
          $.ajax({
            url: "/cancel",
            type: "DELETE",
            data: { student_id: oksched.selectedStudentId(), start_time: event.start.unix() },
            success: oksched.reload
          })
        }
      } else {
        if (window.confirm("Schedule at this time?")) {
          $.post("/match", {
                   student_id: oksched.selectedStudentId(),
                   start_time: event.start.unix(),
                   teacher_id: oksched.selectedTeacherId()
                 }, oksched.reload)
        }
      }
    }
  })
})
