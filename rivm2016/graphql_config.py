from ariadne import QueryType, make_executable_schema, load_schema_from_path, snake_case_fallback_resolvers

import impacts.gql.resolvers

# TODO: move the paths to settings
type_defs = [
    load_schema_from_path("rivm2016/rivm2016.gql"),
    load_schema_from_path("impacts/gql/schema.gql")
]

query = QueryType()


@query.field('hello')
def resolve_hello(*_):
    return "GraphQL service to explore Ecoinvent impact data, compiled by RIVM in 2016."


query.set_field('indicator', impacts.gql.resolvers.resolve_indicator)
query.set_field('indicators', impacts.gql.resolvers.resolve_indicators)

query.set_field('entry', impacts.gql.resolvers.resolve_entry)
query.set_field('entries', impacts.gql.resolvers.resolve_entries)

query.set_field('impact', impacts.gql.resolvers.resolve_impact)

schema = make_executable_schema(
    type_defs,
    query,
    snake_case_fallback_resolvers
)
