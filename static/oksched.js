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
    selectable: false,
    select: function(start, end) {
      $.post("/add", {
               start_time: start.unix(),
               end_time:   end.unix(),
               teacher_id: oksched.selectedTeacherId()
             }, function() {
               oksched.reload()
             })
    },
    editable: false
  })
