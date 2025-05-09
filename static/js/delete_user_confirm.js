document.querySelectorAll('.delete-user-form').forEach(form => {
  form.addEventListener('submit', function (e) {
    e.preventDefault();

    Swal.fire({
      title: 'Are you sure?',
      text: "This user and all their data will be permanently deleted!",
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#d33',
      cancelButtonColor: '#3085d6',
      confirmButtonText: 'Yes, delete user!'
    }).then((result) => {
      if (result.isConfirmed) {
        form.submit();
      }
    });
  });
});