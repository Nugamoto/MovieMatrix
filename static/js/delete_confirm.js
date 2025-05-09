document.querySelectorAll('.delete-form').forEach(form => {
  form.addEventListener('submit', function (e) {
    e.preventDefault(); // Stop form submit

    Swal.fire({
      title: 'Are you sure?',
      text: "This movie will be permanently deleted!",
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#d33',
      cancelButtonColor: '#3085d6',
      confirmButtonText: 'Yes, delete it!'
    }).then((result) => {
      if (result.isConfirmed) {
        form.submit();
      }
    });
  });
});