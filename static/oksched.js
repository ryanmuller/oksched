var oksched = oksched || {}
oksched.selectedTeacherId = function() {
  return $("#teacher").val()
}
oksched.reload = function() {
  $('.calendar').fullCalendar('refetchEvents')
}

$(document).ready(function() {
  $('#teacher').change(oksched.reload)

  $('#teacher-calendar').fullCalendar({
    events: {
      url: '/events',
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
    editable: false
  })

  $('#student-calendar').fullCalendar({
    events: {
      url: '/events',
      data: function() { return { teacher_id: oksched.selectedTeacherId() } }
    },
    defaultView: 'agendaWeek',
    allDaySlot: false,
    defaultTimedEventDuration: "00:30:00",
    selectable: false,
    editable: false,
    eventClick: function(event) {
      if (window.confirm("Schedule at this time?")) {
        $.post("/match", {
                 student_id: 1,
                 start_time: event.start.unix(),
                 teacher_id: oksched.selectedTeacherId()
               }, oksched.reload)
      }
    }
  })
})
