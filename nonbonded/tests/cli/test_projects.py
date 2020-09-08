# @pytest.mark.usefixtures("change_api_url")
# class TestProjectCLI:
#     def test_retrieve(self, requests_mock, runner):
#
#         project = create_project(project_id="project-1")
#         mock_get_project(requests_mock, project)
#
#         arguments = [
#             "retrieve",
#             "--project-id",
#             project.id,
#         ]
#
#         result = runner.invoke(project_cli, arguments)
#
#         if result.exit_code != 0:
#             raise result.exception
#
#         assert result.output.replace("\n", "") == project.json()
#
#     def test_generate(self, requests_mock, runner):
#
#         project = create_project("project-1")
#         project.studies = [create_study("project-1", "study-1")]
#         project.studies[0].benchmarks = [
#             create_benchmark(
#                 "project-1",
#                 "study-1",
#                 "benchmark-1",
#                 ["data-set-1"],
#                 None,
#                 ForceField.from_openff(OFFForceField("openff-1.0.0.offxml")),
#             )
#         ]
#
#         project_json = project.json()
#         project.parse_raw(project_json)
#
#         mock_get_project(requests_mock, project)
#         mock_get_data_set(requests_mock, create_data_set("data-set-1"))
#
#         arguments = [
#             "generate",
#             "--project-id",
#             project.id,
#             "--max-workers",
#             1,
#         ]
#
#         result = runner.invoke(project_cli, arguments)
#
#         if result.exit_code != 0:
#             raise result.exception
#
#     def test_list(self, requests_mock, runner):
#
#         projects = ProjectCollection(projects=[create_project("project-1")])
#         mock_get_projects(requests_mock, projects)
#
#         result = runner.invoke(project_cli, ["list"])
#
#         if result.exit_code != 0:
#             raise result.exception
#
#         assert projects.projects[0].id in result.output
