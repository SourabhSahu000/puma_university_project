/**
 * PUMA University - Client-side Interactive Engine
 */

document.addEventListener("DOMContentLoaded", () => {
    // 1. Mobile Sidebar Toggle & Overlay
    const sidebarToggle = document.getElementById("sidebarToggle");
    const sidebar = document.querySelector(".sidebar");
    const sidebarOverlay = document.getElementById("sidebarOverlay");

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener("click", () => {
            sidebar.classList.toggle("mobile-open");
            if (sidebarOverlay) sidebarOverlay.classList.toggle("active");
        });
    }

    if (sidebarOverlay && sidebar) {
        sidebarOverlay.addEventListener("click", () => {
            sidebar.classList.remove("mobile-open");
            sidebarOverlay.classList.remove("active");
        });
    }

    // 2. Real-time Table Filter / Search
    const searchInputs = document.querySelectorAll("[data-table-search]");
    searchInputs.forEach(input => {
        const targetTableId = input.getAttribute("data-table-search");
        const table = document.getElementById(targetTableId);
        if (!table) return;

        input.addEventListener("input", (e) => {
            const query = e.target.value.toLowerCase().trim();
            const rows = table.querySelectorAll("tbody tr");
            rows.forEach(row => {
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(query) ? "" : "none";
            });
        });
    });

    // 3. Dynamic Cascading Dropdowns (Course -> Semester -> Subject/Student)
    const courseSelects = document.querySelectorAll("[data-cascade-course]");
    courseSelects.forEach(select => {
        select.addEventListener("change", async (e) => {
            const courseId = e.target.value;
            const targetSemSelector = select.getAttribute("data-cascade-course");
            const semSelect = document.querySelector(targetSemSelector);
            if (!semSelect) return;

            semSelect.innerHTML = '<option value="">Loading semesters...</option>';
            if (!courseId) {
                semSelect.innerHTML = '<option value="">Select Course First</option>';
                return;
            }

            try {
                const res = await fetch(`/api/semesters?course_id=${courseId}`);
                const semesters = await res.json();
                semSelect.innerHTML = '<option value="">Select Semester</option>';
                semesters.forEach(sem => {
                    const opt = document.createElement("option");
                    opt.value = sem.id;
                    opt.textContent = `${sem.name} (${sem.course_name || ''})`;
                    semSelect.appendChild(opt);
                });
            } catch (err) {
                console.error("Failed to load semesters:", err);
                semSelect.innerHTML = '<option value="">Error loading semesters</option>';
            }
        });
    });

    // 4. Semester -> Subjects cascading
    const semSelects = document.querySelectorAll("[data-cascade-semester]");
    semSelects.forEach(select => {
        select.addEventListener("change", async (e) => {
            const semesterId = e.target.value;
            const targetSubSelector = select.getAttribute("data-cascade-semester");
            const subSelect = document.querySelector(targetSubSelector);
            if (!subSelect) return;

            subSelect.innerHTML = '<option value="">Loading subjects...</option>';
            if (!semesterId) {
                subSelect.innerHTML = '<option value="">Select Semester First</option>';
                return;
            }

            try {
                const res = await fetch(`/api/subjects?semester_id=${semesterId}`);
                const subjects = await res.json();
                subSelect.innerHTML = '<option value="">Select Subject</option>';
                subjects.forEach(sub => {
                    const opt = document.createElement("option");
                    opt.value = sub.id;
                    opt.textContent = `${sub.name} [${sub.code || 'N/A'}] (${sub.credits} Credits, Max: ${sub.max_marks})`;
                    subSelect.appendChild(opt);
                });
            } catch (err) {
                console.error("Failed to load subjects:", err);
                subSelect.innerHTML = '<option value="">Error loading subjects</option>';
            }
        });
    });

    // 5. SweetAlert2 Confirmation for Delete actions
    const deleteButtons = document.querySelectorAll("[data-confirm-delete]");
    deleteButtons.forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.preventDefault();
            const form = btn.closest("form");
            const entityName = btn.getAttribute("data-confirm-delete") || "this item";

            if (window.Swal) {
                Swal.fire({
                    title: `Delete ${entityName}?`,
                    text: "This action cannot be undone and may remove associated records.",
                    icon: "warning",
                    showCancelButton: true,
                    confirmButtonColor: "#dc2626",
                    cancelButtonColor: "#64748b",
                    confirmButtonText: "Yes, delete it!"
                }).then((result) => {
                    if (result.isConfirmed) {
                        form.submit();
                    }
                });
            } else {
                if (confirm(`Are you sure you want to delete ${entityName}?`)) {
                    form.submit();
                }
            }
        });
    });

    // 6. Dynamic Student -> Relevant Subjects Filter in Marks Entry
    const markStudentSelect = document.getElementById("markStudentSelect");
    const markSubjectSelect = document.getElementById("markSubjectSelect");
    if (markStudentSelect && markSubjectSelect) {
        const allSubjectOptions = Array.from(markSubjectSelect.options).slice(1);
        markStudentSelect.addEventListener("change", () => {
            const selectedOpt = markStudentSelect.options[markStudentSelect.selectedIndex];
            const studentSemId = selectedOpt ? selectedOpt.getAttribute("data-semester") : null;

            markSubjectSelect.innerHTML = '<option value="">Choose Subject</option>';
            if (!studentSemId) {
                allSubjectOptions.forEach(opt => markSubjectSelect.appendChild(opt.cloneNode(true)));
                return;
            }

            const matching = allSubjectOptions.filter(opt => opt.getAttribute("data-semester") === studentSemId);
            const toShow = matching.length > 0 ? matching : allSubjectOptions;
            toShow.forEach(opt => markSubjectSelect.appendChild(opt.cloneNode(true)));
        });
    }
});
